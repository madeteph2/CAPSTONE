from rest_framework import serializers
from .models import Cliente, Pedido, Usuario, HistorialPedido, FichaTecnica, Unidad, Insumo, Receta, Cotizacion, Inventario, MovimientoInventario, Venta, Factura, Pago
from django.db import connection, transaction
from decimal import Decimal


class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = '__all__'


class PedidoSerializer(serializers.ModelSerializer):
    nombre_cliente = serializers.SerializerMethodField()
    nombre_evento = serializers.SerializerMethodField()
    nombre_estado = serializers.SerializerMethodField()
    nombre_responsable = serializers.SerializerMethodField()

    class Meta:
        model = Pedido
        fields = "__all__"

    def get_nombre_cliente(self, obj):
        cliente = obj.id_cliente
        if not cliente:
            return None

        nombre = (cliente.nombre or "").strip()
        apellido = (cliente.apellido or "").strip()
        return f"{nombre} {apellido}".strip()

    def get_nombre_evento(self, obj):
        evento = obj.id_evento
        return evento.nombre_evento if evento else None

    def get_nombre_estado(self, obj):
        estado = obj.id_estado_pedido
        return estado.nombre_estado if estado else None

    def get_nombre_responsable(self, obj):
        usuario = obj.id_usuario_responsable
        if not usuario:
            return None

        nombre = (usuario.nombre or "").strip()
        apellido = (usuario.apellido or "").strip()
        return f"{nombre} {apellido}".strip()


class PedidoWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pedido
        fields = [
            "numero_pedido",
            "fecha_compromiso",
            "fecha_entrega",
            "observaciones",
            "costo_estimado",
            "margen_objetivo",
            "precio_estimado",
            "id_cliente",
            "id_evento",
            "id_estado_pedido",
            "id_usuario_responsable",
        ]
        read_only_fields = ["numero_pedido"]

    def validate(self, attrs):
        attrs = super().validate(attrs)

        cliente = attrs.get(
            "id_cliente",
            getattr(self.instance, "id_cliente", None),
        )

        evento = attrs.get(
            "id_evento",
            getattr(self.instance, "id_evento", None),
        )

        if evento is not None and cliente is not None:
            if evento.id_cliente_id != cliente.pk:
                raise serializers.ValidationError({
                    "id_evento": (
                        "El evento seleccionado no pertenece "
                        "al cliente indicado."
                    )
                })

        return attrs

    def create(self, validated_data):
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT nextval('public.pedido_numero_seq')"
                )
                siguiente_numero = cursor.fetchone()[0]

            numero_pedido = f"PED-{siguiente_numero:04d}"

            return Pedido.objects.create(
                numero_pedido=numero_pedido,
                **validated_data,
            )

class UsuarioSelectorSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = [
            "id_usuario",
            "nombre",
            "apellido",
            "nombre_completo",
        ]

    def get_nombre_completo(self, obj):
        nombre = (obj.nombre or "").strip()
        apellido = (obj.apellido or "").strip()
        return f"{nombre} {apellido}".strip()


class HistorialPedidoSerializer(serializers.ModelSerializer):
    estado_anterior = serializers.CharField(
        source="id_estado_anterior.nombre_estado",
        read_only=True,
        default=None,
    )
    estado_nuevo = serializers.CharField(
        source="id_estado_nuevo.nombre_estado",
        read_only=True,
        default=None,
    )
    usuario = serializers.SerializerMethodField()

    class Meta:
        model = HistorialPedido
        fields = [
            "id_historial_pedido",
            "id_pedido",
            "estado_anterior",
            "estado_nuevo",
            "observacion",
            "usuario",
            "fecha_cambio",
        ]

    def get_usuario(self, obj):
        if not obj.id_usuario:
            return None

        nombre = (obj.id_usuario.nombre or "").strip()
        apellido = (obj.id_usuario.apellido or "").strip()

        return f"{nombre} {apellido}".strip()

# MICA_CATALOGO_V2_5_B1: el backend valida códigos comerciales al guardar fichas.
from mica.catalogo import ETIQUETAS_TIPO


class FichaTecnicaSerializer(serializers.ModelSerializer):
    def validate_tipo_preparacion(self, valor):
        if valor not in (None, '') and valor not in ETIQUETAS_TIPO:
            raise serializers.ValidationError('Seleccione una categoría válida del catálogo.')
        return valor

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if self.instance is None and not attrs.get('tipo_preparacion'):
            raise serializers.ValidationError({'tipo_preparacion': 'Seleccione un tipo de preparación.'})
        return attrs

    class Meta:
        model = FichaTecnica
        fields = "__all__"
        read_only_fields = [
            "id_ficha_tecnica",
            "created_at",
            "updated_at",
        ]

class UnidadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unidad
        fields = ["id_unidad", "nombre_unidad"]


class InsumoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Insumo
        fields = [
            "id_insumo",
            "nombre_insumo",
            "id_unidad",
            "costo_unitario",
            "estado",
        ]

class RecetaSerializer(serializers.ModelSerializer):
    nombre_insumo = serializers.CharField(
        source="id_insumo.nombre_insumo",
        read_only=True
    )
    nombre_unidad = serializers.CharField(
        source="id_unidad.nombre_unidad",
        read_only=True
    )

    class Meta:
        model = Receta
        fields = [
            "id_receta",
            "id_ficha_tecnica",
            "id_insumo",
            "nombre_insumo",
            "cantidad",
            "id_unidad",
            "nombre_unidad",
            "costo_unitario",
            "costo_total",
            "observacion",
        ]
        read_only_fields = [
            "id_receta",
            "id_ficha_tecnica",
            "nombre_insumo",
            "nombre_unidad",
            "costo_unitario",
            "costo_total",
        ]

    def validate(self, attrs):
        attrs = super().validate(attrs)

        for campo in ("cantidad", "costo_unitario", "costo_total"):
            valor = attrs.get(
                campo,
                getattr(self.instance, campo, None)
            )

            if valor is not None:
                minimo = Decimal("0") if campo != "cantidad" else Decimal("0.000001")

                if valor < minimo:
                    raise serializers.ValidationError({
                        campo: "Ingrese un valor válido mayor que cero."
                        if campo == "cantidad"
                        else "El valor no puede ser negativo."
                    })

        # Recalcular costos de receta exclusivamente en backend.
        from mica.services import convertir, dinero
        from django.core.exceptions import ValidationError as CoreValidationError
        insumo = attrs.get('id_insumo', getattr(self.instance, 'id_insumo', None))
        unidad = attrs.get('id_unidad', getattr(self.instance, 'id_unidad', None))
        cantidad = attrs.get('cantidad', getattr(self.instance, 'cantidad', None))
        if insumo and unidad and cantidad is not None:
            try:
                cantidad_en_unidad_insumo = convertir(cantidad, unidad.nombre_unidad, insumo.id_unidad.nombre_unidad)
                costo_x_unidad_receta = convertir(Decimal('1'), unidad.nombre_unidad, insumo.id_unidad.nombre_unidad) * insumo.costo_unitario
            except CoreValidationError as exc:
                raise serializers.ValidationError({'id_unidad': exc.messages})
            attrs['costo_unitario'] = dinero(costo_x_unidad_receta)
            attrs['costo_total'] = dinero(cantidad_en_unidad_insumo * insumo.costo_unitario)
        return attrs

class CotizacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cotizacion
        fields = "__all__"
        read_only_fields = [
            "id_cotizacion",
            "fecha_cotizacion",
        ]

class InventarioSerializer(serializers.ModelSerializer):
    nombre_insumo = serializers.CharField(
        source="id_insumo.nombre_insumo",
        read_only=True
    )

    codigo_insumo = serializers.CharField(
        source="id_insumo.codigo_qr",
        read_only=True
    )

    categoria = serializers.CharField(
        source="id_insumo.categoria",
        read_only=True
    )

    nombre_unidad = serializers.CharField(
        source="id_insumo.id_unidad.nombre_unidad",
        read_only=True
    )

    nivel_stock = serializers.SerializerMethodField()

    class Meta:
        model = Inventario
        fields = "__all__"

    def get_nivel_stock(self, obj):
        if obj.stock_actual < obj.stock_minimo:
            return "critico"

        if obj.stock_actual == obj.stock_minimo:
            return "minimo"

        return "normal"


class MovimientoInventarioSerializer(serializers.ModelSerializer):
    nombre_insumo = serializers.CharField(
        source="id_insumo.nombre_insumo",
        read_only=True
    )

    class Meta:
        model = MovimientoInventario
        fields = "__all__"

# ==========================================
# W12 - VENTAS / FACTURACIÓN
# ==========================================

class VentaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Venta
        fields = "__all__"
        read_only_fields = [
            "id_venta",
            "fecha_venta",
        ]


class FacturaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Factura
        fields = "__all__"
        read_only_fields = [
            "id_factura",
        ]


class PagoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pago
        fields = "__all__"
        read_only_fields = [
            "id_pago",
        ]