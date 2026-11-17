"""Pruebas seguras sin PostgreSQL: contratos de consumidor y protección de datos."""
import json
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch
from django.test import Client, SimpleTestCase
from django.utils import timezone
from mica.publico import DatosEventoPublicoSerializer, propuesta_segura, politica_publica


class CotizadorPublicoTests(SimpleTestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True, HTTP_HOST='127.0.0.1')
        self.datos = {
            'personas': 30, 'presupuesto': '200000',
            'fecha': (timezone.localdate() + timedelta(days=30)).isoformat(),
            'ubicacion': 'Quinta Normal', 'tipo_evento': 'Cumpleaños',
        }

    def test_simulacion_requiere_csrf_aunque_sea_anonima(self):
        r = self.client.post('/api/mica/publico/simular/', data=json.dumps(self.datos), content_type='application/json')
        self.assertEqual(r.status_code, 403)

    def test_envio_requiere_csrf(self):
        r = self.client.post('/api/mica/publico/solicitar/', data='{}', content_type='application/json')
        self.assertEqual(r.status_code, 403)

    def test_restricciones_alimentarias_no_son_ignoradas(self):
        s = DatosEventoPublicoSerializer(data={**self.datos, 'restricciones': ['sin gluten']})
        self.assertFalse(s.is_valid())
        self.assertIn('restricciones', s.errors)

    def test_respuesta_publica_no_filtra_costos(self):
        propuesta = {'id_ficha_tecnica': 5, 'nombre': 'Alternativa 1', 'preparacion': 'Pollo',
                     'personas': 30, 'precio_total': '125000.00', 'precio_persona': '4166.67',
                     'dentro_presupuesto': True, 'requiere_compra': False,
                     'margen': '30', 'costo_total': '85000', 'ingredientes': [{'insumo': 'pollo'}],
                     'costos_servicio': {'costo_personal': '20000'}}
        respuesta = propuesta_segura(propuesta)
        self.assertNotIn('margen', respuesta)
        self.assertNotIn('ingredientes', respuesta)
        self.assertNotIn('costos_servicio', respuesta)
        self.assertNotIn('costo_total', respuesta)

    def test_simulacion_sin_sesion_con_csrf(self):
        # Endpoint de sesión ya entrega csrftoken al navegador.
        self.client.get('/api/auth/session/')
        csrf = self.client.cookies['csrftoken'].value
        ejemplo = {'id_ficha_tecnica': 5, 'nombre': 'Alternativa 1', 'preparacion': 'Pollo',
                   'personas': 30, 'precio_total': '125000.00', 'precio_persona': '4166.67',
                   'dentro_presupuesto': True, 'requiere_compra': False,
                   'costo_total': '85000', 'margen': '30', 'ingredientes': []}
        with patch('mica.publico.simular_publico', return_value=([ejemplo], [], Decimal('30'), {}, ['Aviso'])), \
             patch('mica.publico.explicar', return_value={'modo':'reglas', 'mensaje':'Propuesta de ejemplo.', 'proveedor_activo': False}):
            r = self.client.post('/api/mica/publico/simular/', data=json.dumps(self.datos),
                                 content_type='application/json', HTTP_X_CSRFTOKEN=csrf)
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(r.json()['propuestas'][0]['precio_total'], '125000.00')
        self.assertNotIn('costo_total', r.content.decode('utf8'))

    def test_revisor_requiere_administrador(self):
        r = self.client.post('/api/mica/cotizaciones/1/revision/', data=json.dumps({'accion':'aprobar'}),
                             content_type='application/json')
        self.assertIn(r.status_code, (401, 403))
