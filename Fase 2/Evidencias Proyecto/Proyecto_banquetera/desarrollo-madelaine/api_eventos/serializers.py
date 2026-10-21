
from rest_framework import serializers

from gestion.models import Evento


class EventoWriteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Evento
        fields = [
            "nombre_evento",
            "fecha_evento",
            "hora_evento",
            "direccion",
            "cantidad_personas",
            "observaciones",
            "estado",
            "id_cliente",
        ]

    def validate_cantidad_personas(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError(
                "La cantidad de personas debe ser positiva."
            )
        return value

    def validate_nombre_evento(self, value):
        if not value.strip():
            raise serializers.ValidationError(
                "El nombre del evento es obligatorio."
            )
        return value.strip()

    def validate_direccion(self, value):
        if not value.strip():
            raise serializers.ValidationError(
                "La dirección es obligatoria."
            )
        return value.strip()

    def validate_estado(self, value):
        if not value.strip():
            raise serializers.ValidationError(
                "El estado es obligatorio."
            )
        return value.strip()
