"""Pruebas de contrato de los modelos (sin consultas ni cambios en PostgreSQL)."""
from django.test import SimpleTestCase
from mica.models import PaqueteMica, ComponentePaqueteMica, PropuestaMica


class EsquemaPaquetesV25B2Test(SimpleTestCase):
    def test_propuesta_individual_o_paquete(self):
        self.assertTrue(PropuestaMica._meta.get_field('ficha').null)
        self.assertTrue(PropuestaMica._meta.get_field('paquete').null)
        nombres = {x.name for x in PropuestaMica._meta.constraints}
        self.assertIn('mica_propuesta_ficha_xor_paquete', nombres)

    def test_componentes_por_persona(self):
        campo = ComponentePaqueteMica._meta.get_field('cantidad_por_persona')
        self.assertEqual(campo.decimal_places, 3)
        nombres = {x.name for x in ComponentePaqueteMica._meta.constraints}
        self.assertIn('mica_componente_cantidad_positiva', nombres)
        self.assertIn('mica_componente_paquete_ficha_unica', nombres)

    def test_paquetes_tienen_tipo_y_estado(self):
        opciones = dict(PaqueteMica._meta.get_field('tipo_servicio').choices)
        self.assertIn('coffee_break', opciones)
        self.assertIn('coctel', opciones)
        self.assertTrue(PaqueteMica._meta.get_field('activo').default)
