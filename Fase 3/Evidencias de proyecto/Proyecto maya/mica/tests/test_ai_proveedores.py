"""Pruebas aisladas del adaptador IA: sin claves reales ni acceso a Internet."""
import io
import json
from types import SimpleNamespace, ModuleType
from unittest.mock import patch, MagicMock

from django.test import SimpleTestCase
from mica.ai import explicar

PROPUESTA = SimpleNamespace(
    nombre='Alternativa 1', detalle={'preparacion': 'Pollo'},
    precio_total='50000', dentro_presupuesto=True,
)


class TestAIProveedores(SimpleTestCase):
    def test_sin_credenciales_funciona_con_reglas(self):
        with patch.dict('os.environ', {
            'MICA_IA_PROVEEDOR': 'groq', 'GROQ_API_KEY': '', 'GROQ_MODEL': '',
        }):
            self.assertEqual(explicar([PROPUESTA])['modo'], 'reglas')

    def test_groq_respuesta_sdk_simulada(self):
        modulo = ModuleType('groq')
        groq = MagicMock()
        modulo.Groq = groq
        groq.return_value.chat.completions.create.return_value = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content='Explicación válida'))],
        )
        with patch.dict('sys.modules', {'groq': modulo}):
            with patch.dict('os.environ', {
                'MICA_IA_PROVEEDOR': 'groq', 'GROQ_API_KEY': 'ficticia',
                'GROQ_MODEL': 'openai/gpt-oss-20b',
            }):
                r = explicar([PROPUESTA])
        self.assertEqual(r['modo'], 'ia')
        self.assertEqual(r['proveedor'], 'groq')
        self.assertEqual(r['modelo'], 'openai/gpt-oss-20b')
        llamada = groq.return_value.chat.completions.create.call_args.kwargs
        self.assertEqual(llamada['model'], 'openai/gpt-oss-20b')
        self.assertNotIn('temperature', llamada)

    def test_groq_fallo_sdk_vuelve_a_reglas(self):
        modulo = ModuleType('groq')
        groq = MagicMock()
        modulo.Groq = groq
        groq.return_value.chat.completions.create.side_effect = TimeoutError()
        with patch.dict('sys.modules', {'groq': modulo}):
            with patch.dict('os.environ', {
                'MICA_IA_PROVEEDOR': 'groq', 'GROQ_API_KEY': 'ficticia',
                'GROQ_MODEL': 'openai/gpt-oss-20b',
            }):
                r = explicar([PROPUESTA])
        self.assertEqual(r['modo'], 'reglas')
        self.assertFalse(r['proveedor_activo'])

    @patch('mica.ai.urllib.request.urlopen')
    def test_openai_respuesta_simulada(self, urlopen):
        cuerpo = {'output': [{'type': 'message', 'content': [
            {'type': 'output_text', 'text': 'Texto GPT'},
        ]}]}
        urlopen.return_value.__enter__.return_value = io.BytesIO(json.dumps(cuerpo).encode())
        with patch.dict('os.environ', {
            'MICA_IA_PROVEEDOR': 'openai', 'OPENAI_API_KEY': 'ficticia',
            'OPENAI_MODEL': 'modelo-ejemplo',
        }):
            r = explicar([PROPUESTA])
        self.assertEqual(r['modo'], 'ia')
        self.assertEqual(r['proveedor'], 'openai')
        req = urlopen.call_args[0][0]
        self.assertEqual(req.full_url, 'https://api.openai.com/v1/responses')
        self.assertNotIn('ficticia', req.data.decode())

    def test_modo_reglas_sin_biblioteca(self):
        with patch.dict('os.environ', {'MICA_IA_PROVEEDOR': 'reglas'}):
            r = explicar([PROPUESTA])
        self.assertEqual(r['modo'], 'reglas')
