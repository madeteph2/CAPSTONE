from rest_framework import generics, serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated, DjangoModelPermissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Cliente, Pedido, Usuario, HistorialPedido, FichaTecnica, Unidad, Insumo, Receta, Cotizacion, Inventario, MovimientoInventario, Venta, Factura, Pago
from .serializers import ClienteSerializer, PedidoSerializer, PedidoWriteSerializer, UsuarioSelectorSerializer, HistorialPedidoSerializer, FichaTecnicaSerializer, InsumoSerializer, UnidadSerializer, RecetaSerializer, CotizacionSerializer, InventarioSerializer, MovimientoInventarioSerializer, VentaSerializer, FacturaSerializer, PagoSerializer

from django.db import transaction
from django.utils import timezone

from decimal import Decimal


class ClienteListView(generics.ListAPIView):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticated]


class PedidoListView(generics.ListAPIView):
    queryset = Pedido.objects.select_related(
        "id_cliente",
        "id_evento",
        "id_estado_pedido",
        "id_usuario_responsable",
    ).all()

    serializer_class = PedidoSerializer
    permission_classes = [IsAuthenticated]


class PedidoCreateView(generics.CreateAPIView):
    queryset = Pedido.objects.all()
    serializer_class = PedidoWriteSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]


class PedidoDetailUpdateView(generics.RetrieveUpdateAPIView):
    queryset = Pedido.objects.all()
    permission_classes = [IsAuthenticated, DjangoModelPermissions]
    lookup_field = "id_pedido"

    def get_serializer_class(self):
        if self.request.method == "GET":
            return PedidoSerializer
        return PedidoWriteSerializer

    @transaction.atomic
    def perform_update(self, serializer):
        pedido = self.get_object()

        # Estado anterior antes de guardar
        estado_anterior_id = pedido.id_estado_pedido_id
        from mica.models import CotizacionMica
        
        cot_publica = CotizacionMica.objects.filter(
            pedido=pedido,
            origen='publico'
        ).first()

        destino = serializer.validated_data.get(
            'id_estado_pedido'
        )

        if cot_publica and destino and destino.pk != estado_anterior_id:
            raise serializers.ValidationError({
                'id_estado_pedido': (
                    'Este pedido pertenece a MICA. '
                    'Sus cambios de estado deben realizarse '
                    'mediante el flujo autorizado del Cotizador. '
                    'No se permite modificarlos directamente desde Pedidos.'
                )
            })


        # Guardar los cambios del pedido
        pedido_actualizado = serializer.save()

        # Estado nuevo después de guardar
        estado_nuevo_id = pedido_actualizado.id_estado_pedido_id

        # Registrar historial solo cuando cambie el estado
        if estado_anterior_id != estado_nuevo_id:

            # Relacionar con el usuario autenticado
            usuario = Usuario.objects.filter(
                email=self.request.user.email
            ).first()

            HistorialPedido.objects.create(
                id_pedido=pedido_actualizado,
                id_estado_anterior_id=estado_anterior_id,
                id_estado_nuevo_id=estado_nuevo_id,
                observacion="Cambio de estado realizado desde W05.",
                id_usuario=usuario,
                fecha_cambio=timezone.now(),
            )

            # Sincronizar revisión pública cuando se usa el editor existente de Pedidos.
            # Así ambas interfaces muestran la misma situación comercial.
            from mica.models import CotizacionMica
            cotizacion = CotizacionMica.objects.filter(
                pedido=pedido_actualizado, origen='publico', estado='pendiente_revision'
            ).first()
            if cotizacion:
                nuevo_nombre = pedido_actualizado.id_estado_pedido.nombre_estado.upper()
                if nuevo_nombre in ('CONFIRMADO', 'RECHAZADO'):
                    cotizacion.estado = 'aprobada' if nuevo_nombre == 'CONFIRMADO' else 'rechazada'
                    cotizacion.revisada_por = self.request.user
                    cotizacion.revisada_en = timezone.now()
                    cotizacion.nota_revision = 'Cambio de estado realizado desde Pedidos.'
                    cotizacion.aceptada_en = cotizacion.revisada_en if nuevo_nombre == 'CONFIRMADO' else None
                    cotizacion.save(update_fields=[
                        'estado', 'revisada_por', 'revisada_en', 'nota_revision', 'aceptada_en'
                    ])
                    if cotizacion.evento_id:
                        from .models import Evento
                        Evento.objects.filter(pk=cotizacion.evento_id).update(
                            estado='confirmado' if nuevo_nombre == 'CONFIRMADO' else 'rechazado'
                        )

class UsuarioSelectorListView(generics.ListAPIView):
    serializer_class = UsuarioSelectorSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Usuario.objects.filter(
            estado__iexact="activo"
        ).order_by("nombre", "apellido")

class HistorialPedidoListView(generics.ListAPIView):
    serializer_class = HistorialPedidoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            HistorialPedido.objects
            .filter(id_pedido_id=self.kwargs["id_pedido"])
            .select_related(
                "id_estado_anterior",
                "id_estado_nuevo",
                "id_usuario",
            )
            .order_by("fecha_cambio", "id_historial_pedido")
        )

class FichaTecnicaListView(generics.ListCreateAPIView):
    queryset = FichaTecnica.objects.all().order_by("id_ficha_tecnica")
    serializer_class = FichaTecnicaSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]


class FichaTecnicaDetailView(generics.RetrieveUpdateAPIView):
    queryset = FichaTecnica.objects.all()
    serializer_class = FichaTecnicaSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]
    lookup_field = "id_ficha_tecnica"

class UnidadListView(generics.ListAPIView):
    queryset = Unidad.objects.all().order_by("id_unidad")
    serializer_class = UnidadSerializer
    permission_classes = [IsAuthenticated]


class InsumoListView(generics.ListAPIView):
    queryset = Insumo.objects.filter(
        estado="activo"
    ).order_by("nombre_insumo")

    serializer_class = InsumoSerializer
    permission_classes = [IsAuthenticated]

def sincronizar_costo_ficha(ficha_id):
    """El costo de ficha se recalcula cada vez que cambia una receta."""
    from django.db.models import Sum
    total = Receta.objects.filter(id_ficha_tecnica_id=ficha_id).aggregate(Sum('costo_total'))['costo_total__sum'] or Decimal('0')
    FichaTecnica.objects.filter(id_ficha_tecnica=ficha_id).update(costo_total=total)


class RecetaListCreateView(generics.ListCreateAPIView):
    serializer_class = RecetaSerializer
    permission_classes = [
        IsAuthenticated,
        DjangoModelPermissions,
    ]

    def get_queryset(self):
        return Receta.objects.filter(
            id_ficha_tecnica_id=self.kwargs["id_ficha_tecnica"]
        ).select_related(
            "id_insumo",
            "id_unidad"
        ).order_by("id_receta")

    @transaction.atomic
    def perform_create(self, serializer):
        serializer.save(id_ficha_tecnica_id=self.kwargs["id_ficha_tecnica"])
        sincronizar_costo_ficha(self.kwargs['id_ficha_tecnica'])


class RecetaDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = RecetaSerializer
    permission_classes = [
        IsAuthenticated,
        DjangoModelPermissions,
    ]
    lookup_field = "id_receta"

    @transaction.atomic
    def perform_update(self, serializer):
        obj = serializer.save()
        sincronizar_costo_ficha(obj.id_ficha_tecnica_id)

    @transaction.atomic
    def perform_destroy(self, instance):
        ficha_id = instance.id_ficha_tecnica_id
        instance.delete()
        sincronizar_costo_ficha(ficha_id)

    def get_queryset(self):
        return Receta.objects.filter(
            id_ficha_tecnica_id=self.kwargs["id_ficha_tecnica"]
        )
from django.utils import timezone

class CotizacionListCreateView(generics.ListAPIView):
    queryset = Cotizacion.objects.all().order_by("-id_cotizacion")
    serializer_class = CotizacionSerializer
    permission_classes = [IsAuthenticated]


class CotizacionDetailView(generics.RetrieveAPIView):
    queryset = Cotizacion.objects.all()
    serializer_class = CotizacionSerializer
    lookup_field = "id_cotizacion"
    permission_classes = [IsAuthenticated]

class InventarioListView(generics.ListAPIView):
    queryset = Inventario.objects.select_related(
        "id_insumo",
        "id_insumo__id_unidad",
        "id_bodega",
    ).order_by("id_inventario")

    serializer_class = InventarioSerializer
    permission_classes = [IsAuthenticated]


class MovimientoInventarioListView(generics.ListAPIView):
    queryset = MovimientoInventario.objects.select_related(
        "id_insumo",
        "id_bodega",
    ).order_by("-fecha_movimiento", "-id_movimiento")

    serializer_class = MovimientoInventarioSerializer
    permission_classes = [IsAuthenticated]

class RegistrarMovimientoSerializer(serializers.Serializer):
    id_insumo = serializers.IntegerField(min_value=1)
    id_bodega = serializers.IntegerField(min_value=1)

    tipo_movimiento = serializers.ChoiceField(
        choices=["entrada", "salida"]
    )

    cantidad = serializers.DecimalField(
        max_digits=12,
        decimal_places=3,
        min_value=Decimal("0.001")
    )

    costo_unitario = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0"),
        required=False,
        default=Decimal("0")
    )

    observacion = serializers.CharField(
        required=False,
        allow_blank=True,
        default=""
    )


class RegistrarMovimientoInventarioView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = RegistrarMovimientoSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        datos = serializer.validated_data

        with transaction.atomic():
            inventario = (
                Inventario.objects
                .select_for_update()
                .filter(
                    id_insumo_id=datos["id_insumo"],
                    id_bodega_id=datos["id_bodega"]
                )
                .first()
            )

            if inventario is None:
                return Response(
                    {
                        "error": (
                            "No existe inventario para "
                            "el insumo y bodega indicados."
                        )
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

            cantidad = datos["cantidad"]
            stock_anterior = inventario.stock_actual

            if datos["tipo_movimiento"] == "salida":
                if cantidad > stock_anterior:
                    return Response(
                        {
                            "error": "Stock insuficiente.",
                            "stock_disponible": str(stock_anterior)
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

                inventario.stock_actual = (
                    stock_anterior - cantidad
                )
            else:
                inventario.stock_actual = (
                    stock_anterior + cantidad
                )

            inventario.save(update_fields=["stock_actual"])

            movimiento = MovimientoInventario.objects.create(
                id_insumo_id=datos["id_insumo"],
                id_bodega_id=datos["id_bodega"],
                tipo_movimiento=datos["tipo_movimiento"],
                cantidad=cantidad,
                costo_unitario=datos["costo_unitario"],
                fecha_movimiento=timezone.now(),
                observacion=datos["observacion"]
            )

        return Response(
            {
                "mensaje": "Movimiento registrado correctamente.",
                "id_movimiento": movimiento.id_movimiento,
                "stock_anterior": str(stock_anterior),
                "stock_actual": str(inventario.stock_actual)
            },
            status=status.HTTP_201_CREATED
        )

# ==========================================
# W12 - VENTAS / FACTURACIÓN
# ==========================================

class VentaListView(generics.ListAPIView):
    queryset = Venta.objects.select_related(
        "id_pedido"
    ).order_by("-fecha_venta", "-id_venta")

    serializer_class = VentaSerializer
    permission_classes = [IsAuthenticated]


class FacturaListView(generics.ListAPIView):
    queryset = Factura.objects.select_related(
        "id_venta"
    ).order_by("-fecha_emision", "-id_factura")

    serializer_class = FacturaSerializer
    permission_classes = [IsAuthenticated]


class PagoListView(generics.ListAPIView):
    queryset = Pago.objects.select_related(
        "id_factura"
    ).order_by("-fecha_pago", "-id_pago")

    serializer_class = PagoSerializer
    permission_classes = [IsAuthenticated]