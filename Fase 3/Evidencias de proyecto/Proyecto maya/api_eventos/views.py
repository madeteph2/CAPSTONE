import json
from datetime import date, time

from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods

from gestion.models import Cliente, Evento, Pedido


def serializar_evento(evento):
    cliente = evento.id_cliente
    if cliente.tipo_cliente == "persona_natural":
        nombre_cliente = " ".join(p for p in [cliente.nombre, cliente.apellido] if p)
    else:
        nombre_cliente = cliente.nombre
    return {
        "id_evento": evento.id_evento,
        "nombre_evento": evento.nombre_evento,
        "fecha_evento": evento.fecha_evento.isoformat(),
        "hora_evento": evento.hora_evento.isoformat() if evento.hora_evento else None,
        "direccion": evento.direccion,
        "cantidad_personas": evento.cantidad_personas,
        "observaciones": evento.observaciones,
        "estado": evento.estado,
        "id_cliente": evento.id_cliente_id,
        "nombre_cliente": nombre_cliente,
        "nombre_fantasia": cliente.nombre_fantasia,
    }


@login_required
@require_http_methods(["GET", "POST"])
def eventos(request):
    if request.method == "GET":
        registros = Evento.objects.select_related("id_cliente").order_by("fecha_evento", "id_evento")
        return JsonResponse({
            "total": registros.count(),
            "eventos": [serializar_evento(evento) for evento in registros],
        })

    # Solo usuarios autorizados pueden modificar los datos.
    if not (request.user.is_staff or request.user.is_superuser or request.user.has_perm("gestion.add_evento")):
        return JsonResponse({"detail": "No tiene permiso para registrar eventos."}, status=403)

    try:
        datos = json.loads(request.body)
        if not isinstance(datos, dict):
            raise ValueError
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"detail": "El cuerpo debe ser un objeto JSON válido."}, status=400)

    errores = {}
    nombre = str(datos.get("nombre_evento") or "").strip()
    direccion = str(datos.get("direccion") or "").strip()
    estado = str(datos.get("estado") or "planificado").strip()
    observaciones = str(datos.get("observaciones") or "").strip()
    if not nombre or len(nombre) > 150:
        errores["nombre_evento"] = "Ingrese un nombre de hasta 150 caracteres."
    if not direccion:
        errores["direccion"] = "Ingrese una dirección."
    if not estado or len(estado) > 30:
        errores["estado"] = "Ingrese un estado de hasta 30 caracteres."

    try:
        cliente_id = int(datos.get("id_cliente"))
        cliente = Cliente.objects.get(pk=cliente_id)
    except (TypeError, ValueError, Cliente.DoesNotExist):
        cliente = None
        errores["id_cliente"] = "Seleccione un cliente existente."

    try:
        fecha_evento = date.fromisoformat(str(datos.get("fecha_evento") or ""))
    except ValueError:
        fecha_evento = None
        errores["fecha_evento"] = "Ingrese una fecha válida (AAAA-MM-DD)."

    hora_evento = None
    if datos.get("hora_evento"):
        try:
            hora_evento = time.fromisoformat(str(datos["hora_evento"]))
        except ValueError:
            errores["hora_evento"] = "Ingrese una hora válida."

    cantidad = None
    if datos.get("cantidad_personas") not in (None, ""):
        try:
            cantidad = int(datos["cantidad_personas"])
            if cantidad <= 0:
                raise ValueError
        except (TypeError, ValueError):
            errores["cantidad_personas"] = "Ingrese un número entero positivo."

    if errores:
        return JsonResponse({"detail": "Revise los campos ingresados.", "errors": errores}, status=400)

    ahora = timezone.now()
    try:
        with transaction.atomic():
            evento = Evento.objects.create(
                id_cliente=cliente,
                nombre_evento=nombre,
                fecha_evento=fecha_evento,
                hora_evento=hora_evento,
                direccion=direccion,
                cantidad_personas=cantidad,
                estado=estado,
                observaciones=observaciones,
                created_at=ahora,
                updated_at=ahora,
            )
    except IntegrityError:
        return JsonResponse({"detail": "La base de datos rechazó el registro. Revise los datos."}, status=400)

    return JsonResponse(serializar_evento(evento), status=201)


@login_required
@require_http_methods(["GET", "PATCH", "DELETE"])
def evento_detalle(request, id_evento):
    evento = get_object_or_404(Evento.objects.select_related("id_cliente"), pk=id_evento)
    if request.method == "GET":
        return JsonResponse(serializar_evento(evento))

    if request.method == "DELETE":
        if not (request.user.is_superuser or request.user.has_perm("gestion.delete_evento")):
            return JsonResponse({"detail": "No tiene permiso para eliminar eventos."}, status=403)
        try:
            with transaction.atomic():
                # No borrar eventos vinculados a pedidos, incluso si el FK usa DO_NOTHING.
                if Pedido.objects.filter(id_evento_id=evento.id_evento).exists():
                    return JsonResponse({"detail": "No se puede eliminar: el evento está asociado a uno o más pedidos."}, status=409)
                evento.delete()
        except IntegrityError:
            return JsonResponse({"detail": "No se puede eliminar: existen registros relacionados con este evento."}, status=409)
        return JsonResponse({"detail": "Evento eliminado correctamente."}, status=200)

    if not (request.user.is_superuser or request.user.has_perm("gestion.change_evento")):
        return JsonResponse({"detail": "No tiene permiso para editar eventos."}, status=403)

    try:
        datos = json.loads(request.body)
        if not isinstance(datos, dict):
            raise ValueError
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"detail": "El cuerpo debe ser un objeto JSON válido."}, status=400)

    errores = {}
    actualizaciones = {}
    for campo, limite in (("nombre_evento", 150), ("direccion", None), ("estado", 30)):
        if campo in datos:
            valor = str(datos[campo] or "").strip()
            if not valor or (limite is not None and len(valor) > limite):
                errores[campo] = "Ingrese un valor válido." 
            else:
                actualizaciones[campo] = valor

    if "id_cliente" in datos:
        try:
            actualizaciones["id_cliente"] = Cliente.objects.get(pk=int(datos["id_cliente"]))
        except (TypeError, ValueError, Cliente.DoesNotExist):
            errores["id_cliente"] = "Seleccione un cliente existente."

    if "fecha_evento" in datos:
        try:
            actualizaciones["fecha_evento"] = date.fromisoformat(str(datos["fecha_evento"]))
        except ValueError:
            errores["fecha_evento"] = "Ingrese una fecha válida (AAAA-MM-DD)."

    if "hora_evento" in datos:
        if datos["hora_evento"] in (None, ""):
            actualizaciones["hora_evento"] = None
        else:
            try:
                actualizaciones["hora_evento"] = time.fromisoformat(str(datos["hora_evento"]))
            except ValueError:
                errores["hora_evento"] = "Ingrese una hora válida."

    if "cantidad_personas" in datos:
        if datos["cantidad_personas"] in (None, ""):
            actualizaciones["cantidad_personas"] = None
        else:
            try:
                cantidad = int(datos["cantidad_personas"])
                if cantidad <= 0 or isinstance(datos["cantidad_personas"], bool) or str(datos["cantidad_personas"]).strip() != str(cantidad):
                    raise ValueError
                actualizaciones["cantidad_personas"] = cantidad
            except (TypeError, ValueError):
                errores["cantidad_personas"] = "Ingrese un número entero positivo."

    if "observaciones" in datos:
        actualizaciones["observaciones"] = str(datos["observaciones"] or "").strip()

    # Evitar inconsistencias cliente–evento–pedido al editar.
    nuevo_cliente = actualizaciones.get('id_cliente')
    if nuevo_cliente is not None and nuevo_cliente.pk != evento.id_cliente_id:
        if Pedido.objects.filter(id_evento_id=evento.pk).exclude(id_cliente_id=nuevo_cliente.pk).exists():
            return JsonResponse({'detail': 'No se puede cambiar el cliente: existen pedidos asociados a otro cliente.'}, status=409)
    if errores:
        return JsonResponse({"detail": "Revise los campos ingresados.", "errors": errores}, status=400)
    if not actualizaciones:
        return JsonResponse({"detail": "No se enviaron campos para actualizar."}, status=400)

    try:
        with transaction.atomic():
            for campo, valor in actualizaciones.items():
                setattr(evento, campo, valor)
            evento.updated_at = timezone.now()
            evento.save(update_fields=[*actualizaciones.keys(), "updated_at"])
    except IntegrityError:
        return JsonResponse({"detail": "La base de datos rechazó los cambios."}, status=400)

    evento.refresh_from_db()
    return JsonResponse(serializar_evento(evento))
