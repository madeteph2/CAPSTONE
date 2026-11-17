"""Pruebas de las reglas matemáticas sin modificar la base."""
from decimal import Decimal
from django.test import SimpleTestCase
from mica.consumo import ConsumoError, validar_existencia


class ValidarExistenciaTest(SimpleTestCase):
    def test_pollo(self):
        self.assertEqual(validar_existencia('58.000', '25.000', '25.000'), Decimal('33.000'))

    def test_arroz(self):
        self.assertEqual(validar_existencia('535.000', '7.500', '7.500'), Decimal('527.500'))

    def test_protege_reservas_ajenas(self):
        with self.assertRaises(ConsumoError):
            validar_existencia('20.000', '25.000', '10.000')

    def test_no_acepta_cantidad_cero(self):
        with self.assertRaises(ConsumoError):
            validar_existencia('100', '30', '0')

    def test_exige_reserva_activa(self):
        with self.assertRaises(ConsumoError):
            validar_existencia('100', '3', '5')
