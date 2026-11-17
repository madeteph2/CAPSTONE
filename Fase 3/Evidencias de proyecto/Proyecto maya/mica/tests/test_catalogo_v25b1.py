"""Pruebas independientes de BD para filtros y categorías de MICA v2.5B1."""
from datetime import timedelta
from django.test import SimpleTestCase
from django.utils import timezone
from mica.catalogo import (
    ETIQUETAS_TIPO, TIPOS_POR_GRUPO, filtros_compatibles, grupo_de,
)
from mica.publico import DatosEventoPublicoSerializer


def datos_validos(**otros):
    datos = dict(personas=50, presupuesto='500000.00',
                 fecha=(timezone.localdate() + timedelta(days=30)).isoformat(),
                 ubicacion='Santiago', tipo_evento='Cumpleaños')
    datos.update(otros)
    return datos


class CatalogoV25B1Tests(SimpleTestCase):
    def test_tipos_actuales_conservan_su_grupo(self):
        self.assertEqual(grupo_de('plato_fondo'), 'salados')
        self.assertEqual(grupo_de('acompanamiento'), 'salados')
        self.assertEqual(grupo_de('entrada'), 'salados')
        self.assertEqual(grupo_de('postre'), 'dulces')

    def test_nuevas_bebidas_tienen_grupo_distinto(self):
        self.assertEqual(grupo_de('bebida_fria'), 'bebidas_frias')
        self.assertEqual(grupo_de('bebida_caliente'), 'bebidas_calientes')

    def test_grupo_y_tipo_incompatibles_se_rechazan(self):
        self.assertFalse(filtros_compatibles('salados', 'postre'))
        self.assertFalse(filtros_compatibles('bebidas_frias', 'bebida_caliente'))

    def test_grupo_tipo_validos(self):
        self.assertTrue(filtros_compatibles('salados', 'plato_fondo'))
        self.assertTrue(filtros_compatibles('dulces', 'postre'))
        self.assertEqual(len(ETIQUETAS_TIPO), len(set(sum((list(v) for v in TIPOS_POR_GRUPO.values()), []))))

    def test_api_acepta_grupo_y_tipo_validos(self):
        s = DatosEventoPublicoSerializer(data=datos_validos(grupo='salados', tipo_preparacion='plato_fondo'))
        self.assertTrue(s.is_valid(), s.errors)

    def test_api_rechaza_combinacion_incompatible(self):
        s = DatosEventoPublicoSerializer(data=datos_validos(grupo='salados', tipo_preparacion='postre'))
        self.assertFalse(s.is_valid())
        self.assertIn('tipo_preparacion', s.errors)

    def test_api_rechaza_tipo_desconocido(self):
        s = DatosEventoPublicoSerializer(data=datos_validos(tipo_preparacion='bebida_fria_falsa'))
        self.assertFalse(s.is_valid())
        self.assertIn('tipo_preparacion', s.errors)

    def test_api_antigua_sin_categorias_sigue_admitida(self):
        s = DatosEventoPublicoSerializer(data=datos_validos())
        self.assertTrue(s.is_valid(), s.errors)
        self.assertEqual(s.validated_data['grupo'], '')
