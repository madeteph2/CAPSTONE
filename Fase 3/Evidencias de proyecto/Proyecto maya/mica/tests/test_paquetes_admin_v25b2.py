"""Validaciones de entrada al catálogo; no crean registros de negocio."""
from django.test import SimpleTestCase
from mica.paquetes_api import PaqueteEntradaSerializer


class PaquetesAdminEntradaTest(SimpleTestCase):
    def base(self):
        return {
            'nombre': 'Coffee break básico',
            'tipo_servicio': 'coffee_break',
            'descripcion': 'Servicio de ejemplo',
            'componentes': [
                {'id_ficha_tecnica': 11, 'cantidad_por_persona': '1.000'},
                {'id_ficha_tecnica': 20, 'cantidad_por_persona': '2.000'},
            ],
        }

    def test_paquete_valido(self):
        self.assertTrue(PaqueteEntradaSerializer(data=self.base()).is_valid())

    def test_tipo_inexistente(self):
        dato = self.base(); dato['tipo_servicio'] = 'fiesta_inventada'
        self.assertFalse(PaqueteEntradaSerializer(data=dato).is_valid())

    def test_componente_repetido(self):
        dato = self.base(); dato['componentes'][1]['id_ficha_tecnica'] = 11
        s = PaqueteEntradaSerializer(data=dato)
        self.assertFalse(s.is_valid())
        self.assertIn('componentes', s.errors)

    def test_cantidad_cero(self):
        dato = self.base(); dato['componentes'][0]['cantidad_por_persona'] = '0'
        self.assertFalse(PaqueteEntradaSerializer(data=dato).is_valid())

    def test_cantidad_negativa(self):
        dato = self.base(); dato['componentes'][0]['cantidad_por_persona'] = '-2'
        self.assertFalse(PaqueteEntradaSerializer(data=dato).is_valid())

    def test_sin_componentes(self):
        dato = self.base(); dato['componentes'] = []
        self.assertFalse(PaqueteEntradaSerializer(data=dato).is_valid())

    def test_mas_de_30_componentes(self):
        dato = self.base()
        dato['componentes'] = [
            {'id_ficha_tecnica': n, 'cantidad_por_persona': '1'} for n in range(1, 32)
        ]
        self.assertFalse(PaqueteEntradaSerializer(data=dato).is_valid())

    def test_nombre_vacio(self):
        dato = self.base(); dato['nombre'] = '  '
        self.assertFalse(PaqueteEntradaSerializer(data=dato).is_valid())
