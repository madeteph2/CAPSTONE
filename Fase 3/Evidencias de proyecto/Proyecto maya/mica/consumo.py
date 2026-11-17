"""MICA v2.4 — consumo atómico al iniciar preparación de un pedido público.

Requiere reservas v2.3. SOLO la transición CONFIRMADO -> EN_PREPARACION
consume físicamente; la aprobación sigue reservando sin descontar existencias.
"""
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from gestion.models import (
    EstadoPedido, HistorialPedido, Inventario, MovimientoInventario,
    Pedido, Usuario,
)
from .models import CotizacionMica, ReservaInsumoMica


class ConsumoError(Exception):
    """Conflicto de negocio: la transacción no debe confirmar cambios."""


def validar_existencia(stock_fisico, total_reservado, requerido):
    """Comprueba que este consumo no deje sin respaldo a las otras reservas."""
    stock = Decimal(stock_fisico)
    reservado = Decimal(total_reservado)
    cantidad = Decimal(requerido)
    if cantidad <= 0:
        raise ConsumoError('Existe una reserva con cantidad no positiva.')
    if reservado < cantidad:
        raise ConsumoError('La reserva no coincide con el total activo comprometido.')
    if stock < cantidad or stock < reservado:
        raise ConsumoError(
            'El stock físico no alcanza para consumir el pedido sin perjudicar '
            'otras reservas. Revise los movimientos de inventario.'
        )
    return stock - cantidad


@transaction.atomic
def iniciar_preparacion(cotizacion_id, usuario_django):
    """Consume todas las reservas, crea movimientos e historial en una transacción.

    Bloquea primero cotización y pedido, luego inventarios y reservas.
    Un intento repetido falla con 409 sin crear movimientos adicionales.
    """
    cot = CotizacionMica.objects.select_for_update().filter(
        pk=cotizacion_id, origen='publico'
    ).first()
    if cot is None or cot.estado != 'aprobada' or not cot.pedido_id:
        raise ConsumoError('Solo se pueden preparar solicitudes públicas aprobadas.')

    pedido = Pedido.objects.select_for_update().get(pk=cot.pedido_id)
    anterior = EstadoPedido.objects.get(pk=pedido.id_estado_pedido_id)
    if anterior.nombre_estado.upper() != 'CONFIRMADO':
        raise ConsumoError('El pedido ya no está CONFIRMADO; no puede iniciarse nuevamente.')
    if MovimientoInventario.objects.filter(
        id_pedido=pedido, tipo_movimiento='consumo'
    ).exists():
        raise ConsumoError('Ya existen movimientos de consumo para este pedido. Revise su historial.')

    reservas = list(ReservaInsumoMica.objects.select_for_update().filter(
        pedido=pedido
    ).order_by('id_insumo_id', 'id_bodega_id'))
    if not reservas or any(r.estado != 'reservada' for r in reservas):
        raise ConsumoError('Las reservas del pedido no están completas o ya fueron utilizadas.')

    claves = {(r.id_insumo_id, r.id_bodega_id) for r in reservas}
    if len(claves) != len(reservas):
        raise ConsumoError('Hay reservas duplicadas en el pedido.')
    ids_insumos = sorted({k[0] for k in claves})
    ids_bodegas = sorted({k[1] for k in claves})
    inventarios = list(Inventario.objects.select_for_update().filter(
        id_insumo_id__in=ids_insumos, id_bodega_id__in=ids_bodegas
    ).order_by('id_inventario'))
    por_clave = {(i.id_insumo_id, i.id_bodega_id): i for i in inventarios}
    if not claves.issubset(por_clave):
        raise ConsumoError('Faltan registros de inventario para alguna reserva.')

    # Inventarios bloqueados: las aprobaciones también los bloquean antes de reservar.
    totales = ReservaInsumoMica.objects.filter(
        id_insumo_id__in=ids_insumos, id_bodega_id__in=ids_bodegas,
        estado='reservada'
    ).values('id_insumo_id', 'id_bodega_id').annotate(total=Sum('cantidad'))
    comprometidos = {
        (r['id_insumo_id'], r['id_bodega_id']): r['total']
        for r in totales
    }

    actualizaciones = []
    for reserva in reservas:
        clave = reserva.id_insumo_id, reserva.id_bodega_id
        inventario = por_clave[clave]
        if inventario.estado != 'activo':
            raise ConsumoError('La bodega o el inventario de una reserva ya no está activo.')
        nuevo_stock = validar_existencia(
            inventario.stock_actual,
            comprometidos.get(clave, Decimal('0')),
            reserva.cantidad,
        )
        actualizaciones.append((reserva, inventario, nuevo_stock))

    nuevo_estado = EstadoPedido.objects.filter(
        nombre_estado__iexact='EN_PREPARACION'
    ).first()
    if nuevo_estado is None:
        raise ConsumoError('El catálogo no contiene el estado EN_PREPARACION.')

    usuario = (Usuario.objects.filter(email=usuario_django.email).first()
               if usuario_django.email else None)
    ahora = timezone.now()
    for reserva, inventario, nuevo_stock in actualizaciones:
        inventario.stock_actual = nuevo_stock
        inventario.save(update_fields=['stock_actual'])
        MovimientoInventario.objects.create(
            tipo_movimiento='consumo', fecha_movimiento=ahora,
            cantidad=reserva.cantidad,
            costo_unitario=reserva.id_insumo.costo_unitario,
            observacion=f'MICA v2.4: consumo por inicio de preparación del pedido {pedido.numero_pedido}.',
            id_insumo_id=reserva.id_insumo_id,
            id_bodega_id=reserva.id_bodega_id,
            id_pedido=pedido,
            id_usuario=usuario,
        )
        reserva.estado = 'consumida'
        reserva.save(update_fields=['estado'])

    pedido.id_estado_pedido = nuevo_estado
    pedido.save(update_fields=['id_estado_pedido', 'updated_at'])
    HistorialPedido.objects.create(
        id_pedido=pedido,
        id_estado_anterior=anterior,
        id_estado_nuevo=nuevo_estado,
        id_usuario=usuario,
        fecha_cambio=ahora,
        observacion=f'MICA v2.4: inicio de preparación; {len(actualizaciones)} consumos de inventario.',
    )
    return {
        'pedido_id': pedido.pk,
        'numero_pedido': pedido.numero_pedido,
        'estado_pedido': nuevo_estado.nombre_estado,
        'reservas_consumidas': len(actualizaciones),
        'movimientos_creados': len(actualizaciones),
    }
