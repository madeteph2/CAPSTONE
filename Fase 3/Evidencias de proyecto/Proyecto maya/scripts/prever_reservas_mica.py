"""Diagnóstico de solo lectura: calcula reservas para solicitudes públicas pendientes.

NO aprueba, NO crea reservas y NO descuenta inventario. Realiza bloqueos
transaccionales de lectura para ver stock consistente mientras calcula.
"""
import os
import django
from django.db import connection, transaction

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from mica.models import CotizacionMica, PropuestaMica
from gestion.models import Pedido
from mica.reservas import ReservaError, cantidades_de_propuesta, plan_reservas


def main():
    print('=== PREVISUALIZACIÓN DE RESERVAS MICA ===')
    print('Base:', connection.settings_dict['NAME'])
    if connection.settings_dict['NAME'] != 'sig_banqueteria_mica':
        print('DETENIDO: no se consultará otra base de datos.')
        return
    solicitudes = CotizacionMica.objects.filter(origen='publico', estado='pendiente_revision').order_by('id')
    for c in solicitudes:
        try:
            with transaction.atomic():
                pedido = Pedido.objects.select_for_update().get(pk=c.pedido_id)
                propuesta = PropuestaMica.objects.get(pk=c.propuesta_aceptada, cotizacion=c)
                cantidades = cantidades_de_propuesta(c, propuesta, pedido)
                asignaciones, faltantes = plan_reservas(cantidades)
                print(f'Pedido {pedido.numero_pedido}: {len(cantidades)} insumos; {len(asignaciones)} reservas de bodega posibles; faltantes={faltantes or "NINGUNO"}')
        except (ReservaError, Pedido.DoesNotExist, PropuestaMica.DoesNotExist) as exc:
            print(f'Solicitud #{c.pk}: requiere revisión: {exc}')
    print('DIAGNÓSTICO FINALIZADO. No se modificó ningún registro.')


if __name__ == '__main__':
    main()
