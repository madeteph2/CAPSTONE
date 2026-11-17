from decimal import Decimal
from django.test import SimpleTestCase
from mica.services import seleccionar_propuestas
from mica.publico import propuesta_segura



def p(i, precio, dentro, compra=False):
    return {'id_ficha_tecnica': i, 'nombre': f'Alternativa {i}', 'precio_total': str(precio),
            'dentro_presupuesto': dentro, 'requiere_compra': compra,
            'preparacion': f'Preparación {i}', 'personas': 30,
            'precio_persona': '100.00', 'descripcion': ''}


class RecomendacionesV25ATest(SimpleTestCase):
    def test_lista_vacia_equivale_a_automatico(self):
        opciones = [p(i, i*100, True) for i in range(1, 9)]
        self.assertEqual(len(seleccionar_propuestas(opciones, ids=[])), 3)

    def test_no_recomendar_precio_excedido_si_hay_opciones_validas(self):
        opciones = [p(1, 5000, False), p(2, 900, True), p(3, 1000, True)]
        seleccion = seleccionar_propuestas(opciones)
        self.assertEqual([x['id_ficha_tecnica'] for x in seleccion], [2, 3])

    def test_primero_disponibles_y_luego_reposicion(self):
        opciones = [p(1, 100, True, True), p(2, 500, True), p(3, 600, True)]
        seleccion = seleccionar_propuestas(opciones)
        self.assertEqual([x['id_ficha_tecnica'] for x in seleccion], [2, 3, 1])

    def test_sin_alternativa_presupuestable_muestra_comparativas(self):
        opciones = [p(i, i * 100, False) for i in range(1, 6)]
        seleccion = seleccionar_propuestas(opciones, ids=None)
        self.assertEqual([x['id_ficha_tecnica'] for x in seleccion], [1, 2, 3])
        self.assertTrue(all(not x['dentro_presupuesto'] for x in seleccion))

    def test_ficha_elegida_explicita_se_respeta(self):
        opciones = [p(10, 999, False)]
        self.assertEqual(len(seleccionar_propuestas(opciones, ids=[10])), 1)

    def test_la_api_publica_no_expone_costos_internos(self):
        dato = p(1, 500, True)
        dato['costo_total'] = '200'
        dato['ingredientes'] = [{'insumo': 'secreto'}]
        visible = propuesta_segura(dato)
        self.assertNotIn('costo_total', visible)
        self.assertNotIn('ingredientes', visible)
        self.assertIn('comentario', visible)
