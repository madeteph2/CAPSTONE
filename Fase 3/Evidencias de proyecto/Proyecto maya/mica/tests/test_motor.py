from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch
from django.test import SimpleTestCase
from django.core.exceptions import ValidationError
from mica.services import convertir, precio_minimo, evaluar_ficha, decimal_positivo, margen_minimo
from mica.ai import explicar
# MICA_RESERVAS_V2_3: en pruebas unitarias la tabla de reservas se simula con un mock.


def obj(**kwargs):
    return SimpleNamespace(**kwargs)


class FiltroQuery(list):
    def select_related(self, *args):
        return self

    def order_by(self, *args):
        return self


class MotorTest(SimpleTestCase):
    def test_margen_precio(self):
        self.assertEqual(precio_minimo(Decimal('100000'), Decimal('20')), Decimal('125000.00'))

    def test_conversion_kg_g(self):
        self.assertEqual(convertir('1000', 'g', 'kg'), Decimal('1'))
        self.assertEqual(convertir('1.000', 'kg', 'g'), Decimal('1000.000'))
        with self.assertRaises(ValidationError):
            convertir('1', 'cda.', 'kg')

    def test_cadenas_y_decimal_invalido(self):
        self.assertEqual(decimal_positivo('1.000', 'cantidad'), Decimal('1.000'))
        for n in ('1,000', 'NaN', '-1', 'Infinity', ''):
            with self.subTest(n=n), self.assertRaises(ValidationError):
                decimal_positivo(n, 'cantidad')

    def test_margen_invalido(self):
        with self.assertRaises(ValidationError):
            precio_minimo('1000', '100')

    def test_propuesta_y_stock(self):
        kg = obj(nombre_unidad='kg')
        porciones = obj(nombre_unidad='unidades')
        ins = obj(pk=12, nombre_insumo='Pollo', estado='activo', costo_unitario=Decimal('2000'), id_unidad=kg)
        rec = obj(id_insumo=ins, id_unidad=kg, cantidad=Decimal('1.000'))
        ficha = obj(
            pk=1,
            nombre_ficha='Menú pollo',
            estado='activo',
            tipo_preparacion='plato_fondo',
            id_unidad_rendimiento=porciones,
            rendimiento=Decimal('10')
        )
        costos = {'costo_personal': Decimal('1000'), 'costo_transporte': Decimal('0'), 'otros_costos': Decimal('0')}
        with patch('mica.services.Receta.objects.filter', return_value=FiltroQuery([rec])), patch(
            'mica.services.Inventario.objects.filter', return_value=[obj(stock_actual=Decimal('5'))]), patch(
            'mica.services.ReservaInsumoMica.objects.filter') as reservas:
            reservas.return_value.aggregate.return_value = {'total': Decimal('0')}
            p = evaluar_ficha(ficha, 20, costos, Decimal('20'), Decimal('7000'))
        self.assertEqual(p['precio_total'], '6250.00')
        self.assertTrue(p['dentro_presupuesto'])
        self.assertFalse(p['requiere_compra'])
        self.assertEqual(p['ingredientes'][0]['cantidad'], '2.000')
        with patch('mica.services.Receta.objects.filter', return_value=FiltroQuery([rec])), patch(
            'mica.services.Inventario.objects.filter', return_value=[obj(stock_actual=Decimal('0'))]), patch(
            'mica.services.ReservaInsumoMica.objects.filter') as reservas:
            reservas.return_value.aggregate.return_value = {'total': Decimal('0')}
            p = evaluar_ficha(ficha, 20, costos, Decimal('20'), Decimal('6000'))
        self.assertFalse(p['dentro_presupuesto'])
        self.assertTrue(p['requiere_compra'])
        self.assertEqual(p['exceso_presupuesto'], '250.00')

    def test_respaldo_sin_ia(self):
        p = obj(nombre='Económica', detalle={'preparacion': 'Pollo'}, precio_total=Decimal('1000'), dentro_presupuesto=True)
        with patch.dict('os.environ', {'GROQ_API_KEY': '', 'GROQ_MODEL': ''}):
            self.assertEqual(explicar([p])['modo'], 'reglas')
