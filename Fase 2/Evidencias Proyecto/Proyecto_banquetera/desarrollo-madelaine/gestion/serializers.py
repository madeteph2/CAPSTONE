from rest_framework import serializers
from .models import Cliente, Pedido


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