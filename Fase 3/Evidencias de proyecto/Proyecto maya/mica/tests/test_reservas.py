"""Pruebas unitarias de asignación de stock. No alteran PostgreSQL."""
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch
from django.test import SimpleTestCase
from mica.reservas import plan_reservas


class ReservaPlanTests(SimpleTestCase):
    def _ejecutar(self, stock, comprometido, solicitud):
        filas = [SimpleNamespace(id_insumo_id=1, id_bodega_id=2,
                                 stock_actual=Decimal(stock))]
        with patch('mica.reservas.Inventario.objects.select_for_update') as inventario, \
                patch('mica.reservas.ReservaInsumoMica.objects.filter') as reservas:
            inventario.return_value.filter.return_value.order_by.return_value = filas
            reservas.return_value.values.return_value.annotate.return_value = (
                [{'id_insumo_id': 1, 'id_bodega_id': 2, 'total': Decimal(comprometido)}]
                if Decimal(comprometido) else []
            )
            return plan_reservas({1: Decimal(solicitud)})

    def test_reservar_no_disminuye_el_stock(self):
        asignaciones, faltantes = self._ejecutar('20', '0', '12')
        self.assertEqual(asignaciones, [(1, 2, Decimal('12'))])
        self.assertFalse(faltantes)

    def test_dos_pedidos_no_comparten_los_mismos_ingredientes(self):
        asignaciones, faltantes = self._ejecutar('20', '15', '12')
        self.assertEqual(asignaciones, [(1, 2, Decimal('5'))])
        self.assertEqual(faltantes, {'1': '7'})

    def test_stock_comprometido_nunca_se_considera_libre(self):
        asignaciones, faltantes = self._ejecutar('10', '10', '5')
        self.assertEqual(asignaciones, [])
        self.assertEqual(faltantes, {'1': '5'})
