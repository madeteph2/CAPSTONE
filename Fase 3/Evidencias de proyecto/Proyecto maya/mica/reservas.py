"""Reservas de ingredientes del pedido MICA.

Reserva no equivale a consumo: inventario.stock_actual permanece intacto.
Las reservas usan SELECT FOR UPDATE de inventarios para serializar aprobaciones.
Solo PostgreSQL y Django admin autorizados pueden crear reservas.
"""
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

from django.core.exceptions import ValidationError
from django.db.models import Sum

from gestion.models import Inventario, Receta, DetallePedido
from .models import ReservaInsumoMica
from .services import convertir

TRES_DECIMALES = Decimal('0.001')


class ReservaError(Exception):
    """Error de negocio sin cambios confirmados en la base."""


def cantidades_de_propuesta(cotizacion, propuesta, pedido):
    """Extrae cantidades del snapshot y comprueba que el pedido/receta no cambió."""
    if propuesta.cotizacion_id != cotizacion.pk or cotizacion.pedido_id != pedido.pk:
        raise ReservaError('La propuesta no corresponde a este pedido.')
    detalles = list(DetallePedido.objects.filter(id_pedido=pedido).order_by('id_detalle_pedido'))
    if len(detalles) != 1 or detalles[0].id_ficha_tecnica_id != propuesta.ficha_id or detalles[0].tipo_detalle != 'ficha_tecnica' or Decimal(detalles[0].cantidad) != 1:
        raise ReservaError('El detalle del pedido fue modificado. Recalcule la propuesta antes de reservar insumos.')
    if (Decimal(pedido.precio_estimado) != Decimal(propuesta.precio_total)
            or Decimal(pedido.costo_estimado) != Decimal(propuesta.costo_total)):
        raise ReservaError('Los importes del pedido cambiaron. Se necesita validar una nueva cotización antes de reservar.')
    if cotizacion.evento_id and cotizacion.evento.cantidad_personas != cotizacion.personas:
        raise ReservaError('Se modificó la cantidad de comensales del evento. Es necesario recalcular la cotización.')
    esperado = defaultdict(Decimal)
    for ingrediente in propuesta.detalle.get('ingredientes', []):
        try:
            insumo_id = int(ingrediente['id_insumo'])
            cantidad = Decimal(str(ingrediente['cantidad']))
        except (KeyError, ValueError, TypeError, InvalidOperation) as exc:
            raise ReservaError('Hay ingredientes inválidos en la propuesta guardada.') from exc
        if not cantidad.is_finite() or cantidad <= 0 or cantidad != cantidad.quantize(TRES_DECIMALES):
            raise ReservaError('Una cantidad del snapshot es inválida o excede tres decimales.')
        esperado[insumo_id] += cantidad
    if not esperado:
        raise ReservaError('La propuesta no contiene insumos para reservar.')
    recetas = list(Receta.objects.filter(id_ficha_tecnica_id=propuesta.ficha_id).select_related(
        'id_insumo__id_unidad', 'id_unidad', 'id_ficha_tecnica'))
    if not recetas:
        raise ReservaError('La ficha ya no tiene receta asociada.')
    vigentes = defaultdict(Decimal)
    try:
        for receta in recetas:
            factor = Decimal(cotizacion.personas) / Decimal(receta.id_ficha_tecnica.rendimiento)
            cantidad = convertir(
                Decimal(receta.cantidad) * factor,
                receta.id_unidad.nombre_unidad,
                receta.id_insumo.id_unidad.nombre_unidad,
            ).quantize(TRES_DECIMALES, rounding=ROUND_HALF_UP)
            vigentes[receta.id_insumo_id] += cantidad
    except (ValueError, InvalidOperation, ZeroDivisionError, ValidationError) as exc:
        raise ReservaError('La receta actual no se puede validar; revise rendimiento y unidades.') from exc
    if dict(esperado) != dict(vigentes):
        raise ReservaError('La receta cambió desde la cotización. Recalcule antes de aprobar y reservar.')
    return dict(esperado)


def plan_reservas(cantidades):
    """SOLO LLAMAR dentro de transaction.atomic(). Bloquea inventarios hasta el commit."""
    ids = sorted(cantidades)
    inventarios = list(Inventario.objects.select_for_update().filter(
        id_insumo_id__in=ids, estado='activo'
    ).order_by('id_insumo_id', 'id_bodega_id', 'id_inventario'))
    reservas_activas = ReservaInsumoMica.objects.filter(
        id_insumo_id__in=ids, estado='reservada'
    ).values('id_insumo_id', 'id_bodega_id').annotate(total=Sum('cantidad'))
    comprometido = {
        (r['id_insumo_id'], r['id_bodega_id']): r['total'] for r in reservas_activas
    }
    asignaciones, faltantes = [], {}
    for insumo_id in ids:
        pendiente = cantidades[insumo_id]
        for inv in inventarios:
            if inv.id_insumo_id != insumo_id or pendiente <= 0:
                continue
            libre = max(Decimal('0'), Decimal(inv.stock_actual) - comprometido.get((insumo_id, inv.id_bodega_id), Decimal('0')))
            a_reservar = min(libre, pendiente)
            if a_reservar > 0:
                asignaciones.append((insumo_id, inv.id_bodega_id, a_reservar))
                pendiente -= a_reservar
        if pendiente > 0:
            faltantes[str(insumo_id)] = str(pendiente)
    return asignaciones, faltantes


def reservar_pedido(cotizacion, propuesta, pedido):
    """Llamar dentro de una transacción con el pedido bloqueado.

    No crea reservas parciales: si falta cualquier ingrediente, retorna error.
    """
    if ReservaInsumoMica.objects.filter(pedido=pedido).exists():
        raise ReservaError('Este pedido ya tiene reservas; no se pueden crear nuevamente.')
    cantidades = cantidades_de_propuesta(cotizacion, propuesta, pedido)
    asignaciones, faltantes = plan_reservas(cantidades)
    if faltantes:
        raise ReservaError(
            'Inventario disponible insuficiente para reservar el pedido. '
            f'Faltantes (id_insumo: cantidad): {faltantes}. '
            'Registre entradas de stock y vuelva a aprobar. Confirmar una compra no aumenta el inventario.'
        )
    if not asignaciones:
        raise ReservaError('No hay existencias disponibles para reservar.')
    ReservaInsumoMica.objects.bulk_create([
        ReservaInsumoMica(pedido=pedido, id_insumo_id=insumo_id, id_bodega_id=bodega_id,
                          cantidad=cantidad, estado='reservada')
        for insumo_id, bodega_id, cantidad in asignaciones
    ])
    return len(asignaciones)


def liberar_reservas(pedido):
    """Liberar reservas sin alterar stock físico. Transacción + pedido bloqueado."""
    return ReservaInsumoMica.objects.filter(pedido=pedido, estado='reservada').update(estado='liberada')
