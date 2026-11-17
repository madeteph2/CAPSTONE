"""Motor MICA determinista. No depende de IA. Cantidades/moneda con Decimal."""
import os
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from django.core.exceptions import ValidationError
from gestion.models import FichaTecnica, Receta, Inventario
from django.db.models import Sum
from .models import ReservaInsumoMica  # MICA_RESERVAS_V2_3
from .catalogo import TIPOS_POR_GRUPO  # MICA_CATALOGO_V2_5_B1

CENTAVO = Decimal('0.01')
MIL = Decimal('1000')
MAPA = {
    'kg': ('masa', Decimal('1000')), 'g': ('masa', Decimal('1')),
    'lt': ('volumen', Decimal('1000')), 'l': ('volumen', Decimal('1000')),
    'ml': ('volumen', Decimal('1')),
    'unidad': ('pieza', Decimal('1')), 'unidades': ('pieza', Decimal('1')),
    'porciones': ('pieza', Decimal('1')), 'porción': ('pieza', Decimal('1')),
}


def decimal_positivo(valor, nombre, permitir_cero=False):
    try:
        # Formato de API: separador decimal '.', nunca interpretamos miles.
        if isinstance(valor, bool) or isinstance(valor, float):
            raise ValueError
        texto = str(valor).strip()
        if not texto or ',' in texto:
            raise ValueError
        numero = Decimal(texto)
        if not numero.is_finite() or (numero < 0 if permitir_cero else numero <= 0):
            raise ValueError
        return numero
    except (InvalidOperation, ValueError, TypeError):
        raise ValidationError(f'{nombre}: número decimal inválido; use punto decimal, sin miles.')


def dinero(valor):
    return Decimal(valor).quantize(CENTAVO, rounding=ROUND_HALF_UP)


def convertir(cantidad, unidad_origen, unidad_destino):
    a = MAPA.get(str(unidad_origen).strip().lower())
    b = MAPA.get(str(unidad_destino).strip().lower())
    if not a or not b or a[0] != b[0]:
        raise ValidationError(f'Conversión no definida: {unidad_origen} a {unidad_destino}.')
    return Decimal(cantidad) * a[1] / b[1]


def precio_minimo(costo_total, porcentaje):
    margen = decimal_positivo(porcentaje, 'margen', permitir_cero=True)
    if margen >= 100:
        raise ValidationError('El margen debe ser menor que 100%.')
    return dinero(Decimal(costo_total) / (Decimal('1') - margen / 100))


def margen_minimo():
    n = decimal_positivo(os.environ.get('MICA_MARGEN_MINIMO', '30'), 'MICA_MARGEN_MINIMO', permitir_cero=True)
    if n >= 100:
        raise ValidationError('MICA_MARGEN_MINIMO debe ser menor que 100.')
    return n


def evaluar_ficha(ficha, personas, costos, margen, presupuesto):
    """Devuelve snapshot reconstruible o error de validación explícito."""
    if ficha.estado.lower() != 'activo':
        raise ValidationError('La ficha no está activa.')
    if not ficha.id_unidad_rendimiento or not ficha.id_unidad_rendimiento.nombre_unidad.lower() in ('unidades', 'unidad', 'porciones', 'porción'):
        raise ValidationError('El rendimiento debe estar expresado en porciones/unidades antes de cotizar.')
    rinde = decimal_positivo(ficha.rendimiento, 'rendimiento')
    factor = Decimal(personas) / rinde
    recetas = list(Receta.objects.filter(id_ficha_tecnica=ficha).select_related('id_insumo__id_unidad', 'id_unidad').order_by('id_receta'))
    if not recetas:
        raise ValidationError('La ficha no tiene ingredientes registrados.')
    lineas = []
    costo_insumos = Decimal('0')
    for receta in recetas:
        insumo = receta.id_insumo
        if insumo.estado.lower() != 'activo':
            raise ValidationError(f'Insumo inactivo: {insumo.nombre_insumo}.')
        costo_unitario = decimal_positivo(insumo.costo_unitario, f'Costo de {insumo.nombre_insumo}')
        cantidad_receta = decimal_positivo(receta.cantidad, f'Cantidad de {insumo.nombre_insumo}')
        unidades = convertir(cantidad_receta * factor, receta.id_unidad.nombre_unidad, insumo.id_unidad.nombre_unidad)
        subtotal = dinero(unidades * costo_unitario)
        # Disponible = físico - reservas activas; la simulación nunca descuenta stock.
        stock_fisico = sum((Decimal(i.stock_actual) for i in Inventario.objects.filter(id_insumo=insumo, estado='activo')), Decimal('0'))
        comprometido = ReservaInsumoMica.objects.filter(id_insumo=insumo, estado='reservada').aggregate(total=Sum('cantidad'))['total'] or Decimal('0')
        stock = max(Decimal('0'), stock_fisico - Decimal(comprometido))
        lineas.append({
            'id_insumo': insumo.pk, 'insumo': insumo.nombre_insumo,
            'cantidad': str(unidades.quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)),
            'unidad': insumo.id_unidad.nombre_unidad,
            'costo_unitario': str(costo_unitario), 'subtotal': str(subtotal),
            'stock_consultado': str(stock), 'faltante': str(max(Decimal('0'), unidades - stock).quantize(Decimal('0.001'), rounding=ROUND_HALF_UP))
        })
        costo_insumos += subtotal
    costo_total = dinero(costo_insumos + sum(costos.values()))
    precio_total = precio_minimo(costo_total, margen)
    presupuesto = Decimal(presupuesto)
    faltante_presupuesto = max(Decimal('0'), precio_total - presupuesto)
    return {
        'id_ficha_tecnica': ficha.pk,
        'preparacion': ficha.nombre_ficha,
        'tipo_preparacion': ficha.tipo_preparacion or '',
        'descripcion': str(getattr(ficha, 'descripcion', '') or '')[:250],
        'rendimiento_original': str(rinde),
        'personas': int(personas),
        'factor': str(factor),
        'ingredientes': lineas,
        'costo_insumos': str(dinero(costo_insumos)),
        'costos_servicio': {k: str(v) for k, v in costos.items()},
        'costo_total': str(costo_total),
        'margen': str(margen), 'precio_total': str(precio_total),
        'precio_persona': str(dinero(precio_total / Decimal(personas))),
        'dentro_presupuesto': precio_total <= presupuesto,
        'exceso_presupuesto': str(dinero(faltante_presupuesto)),
        'requiere_compra': any(Decimal(x['faltante']) > 0 for x in lineas),
        'condiciones': [
            'Cotización preliminar; inventario consultado, no reservado.',
            'Se requiere validar compras, alérgenos y contaminación cruzada antes de confirmar.',
            'Precios calculados desde insumos vigentes al momento de simular.'
        ]
    }


def _diversificar_por_precio(opciones, limite):
    """Hasta `limite` opciones económicas/intermedias/altas entre las ya filtradas."""
    if limite <= 0:
        return []
    if len(opciones) <= limite:
        return list(opciones)
    if limite == 1:
        return [opciones[0]]
    posiciones = [(i * (len(opciones) - 1)) // (limite - 1) for i in range(limite)]
    return [opciones[i] for i in posiciones]


def seleccionar_propuestas(propuestas, ids=None, limite=3):
    """MICA_RECOMENDACIONES_V2_5_A: selección comercial sin modificar cálculos.

    Presupuesto y disponibilidad primero. Si hay opciones dentro de presupuesto,
    no se muestran opciones que lo exceden; se prioriza stock libre. En ausencia
    de opciones dentro del presupuesto se muestran comparativas no seleccionables.
    La selección explícita de ficha preserva su comportamiento anterior.
    """
    ordenadas = sorted(propuestas, key=lambda p: (Decimal(p['precio_total']), p['id_ficha_tecnica']))
    if ids:  # ficha elegida explícitamente por la persona
        elegidas = ordenadas
    else:    # incluye ids=None e ids=[] enviados por el formulario público
        bajo_presupuesto = [p for p in ordenadas if p['dentro_presupuesto']]
        if bajo_presupuesto:
            stock = [p for p in bajo_presupuesto if not p['requiere_compra']]
            reposicion = [p for p in bajo_presupuesto if p['requiere_compra']]
            elegidas = _diversificar_por_precio(stock, limite)
            elegidas += _diversificar_por_precio(reposicion, limite - len(elegidas))
        else:
            elegidas = ordenadas[:limite]
    for i, propuesta in enumerate(elegidas, 1):
        propuesta['nombre'] = f'Alternativa {i}'
    return elegidas


def generar_propuestas(*, personas, presupuesto, margen, costos, ids=None, grupo="", tipo_preparacion=""):
    """Preparaciones individuales; stock y presupuesto comprobados por Django."""
    propuestas, descartadas = [], []
    fichas = FichaTecnica.objects.select_related('id_unidad_rendimiento').filter(estado__iexact='activo')
    # MICA_CATALOGO_V2_5_B1: filtro autoritativo también para POST solicitar.
    if grupo:
        fichas = fichas.filter(tipo_preparacion__in=TIPOS_POR_GRUPO.get(grupo, ()))
    if tipo_preparacion:
        fichas = fichas.filter(tipo_preparacion=tipo_preparacion)
    if ids:
        fichas = fichas.filter(id_ficha_tecnica__in=ids)
    for ficha in fichas.order_by('id_ficha_tecnica'):
        try:
            propuestas.append(evaluar_ficha(ficha, personas, costos, margen, presupuesto))
        except ValidationError as exc:
            descartadas.append({'id_ficha_tecnica': ficha.pk, 'motivo': '; '.join(exc.messages)})
    return seleccionar_propuestas(propuestas, ids=ids, limite=3), descartadas
