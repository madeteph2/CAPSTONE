
import json

from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods

from gestion.models import Evento, Pedido
from .serializers import EventoWriteSerializer


# Convertir un evento a JSON
def serializar_evento(evento):
    cliente = evento.id_cliente

    if cliente.tipo_cliente == "persona_natural":
        nombre_cliente = " ".join(
            parte for parte in [
                cliente.nombre,
                cliente.apellido,
            ]
            if parte
        )
    else:
        nombre_cliente = cliente.nombre

    return {
        "id_evento": evento.id_evento,
        "nombre_evento": evento.nombre_evento,
        "fecha_evento": evento.fecha_evento.isoformat(),
        "hora_evento": (
            evento.hora_evento.isoformat()
            if evento.hora_evento else None
        ),
        "direccion": evento.direccion,
        "cantidad_personas": evento.cantidad_personas,
        "observaciones": evento.observaciones,
        "estado": evento.estado,
        "id_cliente": evento.id_cliente_id,
        "nombre_cliente": nombre_cliente,
        "nombre_fantasia": cliente.nombre_fantasia,
    }


# Verificar permisos de escritura
def puede_escribir(usuario):
    return (
        usuario.is_authenticated
        and usuario.is_active
        and (usuario.is_staff or usuario.is_superuser)
    )


# Leer JSON recibido
def leer_json(request):
    try:
        datos = json.loads(request.body)
    except (ValueError, UnicodeDecodeError):
        return None

    return datos if isinstance(datos, dict) else None


# GET: listar eventos
# POST: crear evento
@login_required
@csrf_protect
@require_http_methods(["GET", "POST"])
def eventos(request):

    if request.method == "GET":

        registros = (
            Evento.objects
            .select_related("id_cliente")
            .order_by("fecha_evento", "id_evento")
        )

        return JsonResponse({
            "total": registros.count(),
            "eventos": [
                serializar_evento(evento)
                for evento in registros
            ],
        })

    # Desde aquí se procesa POST
    if not puede_escribir(request.user):
        return JsonResponse(
            {"detail": "No tiene permisos para crear eventos."},
            status=403,
        )

    datos = leer_json(request)

    if datos is None:
        return JsonResponse(
            {"detail": "Debe enviar un objeto JSON válido."},
            status=400,
        )

    serializer = EventoWriteSerializer(data=datos)

    if not serializer.is_valid():
        return JsonResponse(
            {
                "detail": "Existen errores de validación.",
                "errors": serializer.errors,
            },
            status=400,
        )

    ahora = timezone.now()

    try:
        with transaction.atomic():
            evento = serializer.save(
                created_at=ahora,
                updated_at=ahora,
            )
    except IntegrityError:
        return JsonResponse(
            {
                "detail": (
                    "No se pudo guardar el evento. "
                    "Revise las restricciones de PostgreSQL."
                )
            },
            status=409,
        )

    evento = (
        Evento.objects
        .select_related("id_cliente")
        .get(pk=evento.pk)
    )

    return JsonResponse(
        serializar_evento(evento),
        status=201,
    )


# GET: consultar evento
# PATCH: editar evento
@login_required
@csrf_protect
@require_http_methods(["GET", "PATCH"])
def evento_detalle(request, id_evento):

    evento = get_object_or_404(
        Evento.objects.select_related("id_cliente"),
        pk=id_evento,
    )

    if request.method == "GET":
        return JsonResponse(serializar_evento(evento))

    # Desde aquí se procesa PATCH
    if not puede_escribir(request.user):
        return JsonResponse(
            {"detail": "No tiene permisos para editar eventos."},
            status=403,
        )

    datos = leer_json(request)

    if datos is None:
        return JsonResponse(
            {"detail": "Debe enviar un objeto JSON válido."},
            status=400,
        )

    serializer = EventoWriteSerializer(
        evento,
        data=datos,
        partial=True,
    )

        
    if not serializer.is_valid():
        return JsonResponse(
            {
                "detail": "Existen errores de validación.",
                "errors": serializer.errors,
            },
            status=400,
        )

    if not serializer.validated_data:
        return JsonResponse(
            {"detail": "No se enviaron cambios."},
            status=400,
        )

    # Evitar cambiar el cliente cuando existen pedidos asociados.
    cliente_nuevo = serializer.validated_data.get("id_cliente")

    if (
        cliente_nuevo is not None
        and cliente_nuevo.pk != evento.id_cliente_id
        and Pedido.objects.filter(id_evento=evento).exists()
    ):
        return JsonResponse(
            {
                "detail": (
                    "No se puede cambiar el cliente del evento "
                    "porque tiene pedidos asociados."
                )
            },
            status=409,
        )


    if not serializer.validated_data:
        return JsonResponse(
            {"detail": "No se enviaron cambios."},
            status=400,
        )

    try:
        with transaction.atomic():
            evento = serializer.save(
                updated_at=timezone.now()
            )
    except IntegrityError:
        return JsonResponse(
            {
                "detail": (
                    "No se pudo actualizar el evento. "
                    "Revise las restricciones de PostgreSQL."
                )
            },
            status=409,
        )

    evento.refresh_from_db()

    return JsonResponse(serializar_evento(evento))
