"""Flujo de consumidor MICA: público, sin acceso a costos internos.

Simulación -> selección -> pedido CREADO pendiente de revisión -> aprobación por personal.
Las operaciones de creación son atómicas y no confían en cifras enviadas por el cliente.
"""
import os
from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import connection, transaction
from django.db.models import Sum
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from gestion.models import Cliente, Evento, EstadoPedido, Pedido, HistorialPedido, Usuario, FichaTecnica
from .models import CotizacionMica, PropuestaMica, ReservaInsumoMica
from .services import decimal_positivo, dinero, generar_propuestas, margen_minimo
from .catalogo import TIPOS_POR_GRUPO, TODOS_TIPOS, grupo_de, filtros_compatibles  # MICA_CATALOGO_V2_5_B1
from .ai import explicar
from .reservas import reservar_pedido, liberar_reservas, ReservaError  # MICA_RESERVAS_V2_3


class DatosEventoPublicoSerializer(serializers.Serializer):
    personas = serializers.IntegerField(min_value=1, max_value=2000)
    presupuesto = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal('1'))
    fecha = serializers.DateField()
    ubicacion = serializers.CharField(max_length=300, trim_whitespace=True)
    tipo_evento = serializers.CharField(max_length=100, trim_whitespace=True)
    ficha_ids = serializers.ListField(child=serializers.IntegerField(min_value=1), required=False)
    grupo = serializers.ChoiceField(choices=list(TIPOS_POR_GRUPO), required=False, allow_blank=True, default='')
    tipo_preparacion = serializers.ChoiceField(choices=list(TODOS_TIPOS), required=False, allow_blank=True, default='')
    restricciones = serializers.ListField(child=serializers.CharField(max_length=100), required=False, default=list)

    def validate(self, attrs):
        if attrs['fecha'] < timezone.localdate():
            raise serializers.ValidationError({'fecha': 'La fecha no puede ser anterior a hoy.'})
        if not attrs['ubicacion'].strip() or not attrs['tipo_evento'].strip():
            raise serializers.ValidationError({'ubicacion': 'Indique ubicación y tipo de evento.'})
        if attrs.get('restricciones'):
            raise serializers.ValidationError({'restricciones': 'Se requiere evaluación humana de alergias o restricciones alimentarias antes de cotizar. Contacte al personal.'})
        if not filtros_compatibles(attrs.get('grupo', ''), attrs.get('tipo_preparacion', '')):
            raise serializers.ValidationError({'tipo_preparacion': 'El tipo de preparación no corresponde al grupo seleccionado.'})
        return attrs


class EnviarSolicitudPublicaSerializer(DatosEventoPublicoSerializer):
    nombre = serializers.CharField(max_length=150)
    apellido = serializers.CharField(max_length=100)
    email = serializers.EmailField(max_length=150)
    telefono = serializers.CharField(max_length=30)
    comentario = serializers.CharField(max_length=1500, required=False, allow_blank=True, default='')
    ficha_id = serializers.IntegerField(min_value=1)
    precio_mostrado = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal('1'))
    acepta_condiciones = serializers.BooleanField()
    identificador = serializers.UUIDField(required=False)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if not attrs['acepta_condiciones']:
            raise serializers.ValidationError({'acepta_condiciones': 'Debe aceptar el uso de sus datos para gestionar la solicitud.'})
        if len(''.join(ch for ch in attrs['telefono'] if ch.isdigit())) < 8:
            raise serializers.ValidationError({'telefono': 'Ingrese un teléfono de contacto válido.'})
        if attrs.get('ficha_ids') and attrs['ficha_id'] not in attrs['ficha_ids']:
            raise serializers.ValidationError({'ficha_id': 'La ficha seleccionada no corresponde a la simulación.'})
        return attrs


def politica_publica():
    """Parámetros controlados por administración; nunca llegan desde el navegador."""
    costos = {}
    for campo, clave in (
        ('costo_personal', 'MICA_PUBLICO_COSTO_PERSONAL'),
        ('costo_transporte', 'MICA_PUBLICO_COSTO_TRANSPORTE'),
        ('otros_costos', 'MICA_PUBLICO_OTROS_COSTOS'),
    ):
        costos[campo] = dinero(decimal_positivo(os.environ.get(clave, '0'), clave, permitir_cero=True))
    advertencias = [
        'Precios preliminares sujetos a validación del personal; no se confirma el servicio ni se reserva stock.',
        'La disponibilidad del menú, compras y seguridad alimentaria requieren validación antes de aprobar.',
        'No incluye impuestos ni servicios no configurados; el personal confirmará el alcance y precio final.',
    ]
    if all(not x for x in costos.values()):
        advertencias.append('Estimación de demostración: aún no se configuraron cargos por personal, transporte y otros servicios.')
    return margen_minimo(), costos, advertencias


def simular_publico(datos):
    margen, costos, advertencias = politica_publica()
    propuestas, descartadas = generar_propuestas(
        personas=datos['personas'], presupuesto=datos['presupuesto'], margen=margen,
        costos=costos, ids=datos.get('ficha_ids'),
        grupo=datos.get('grupo', ''), tipo_preparacion=datos.get('tipo_preparacion', ''),
    )
    return propuestas, descartadas, margen, costos, advertencias


def propuesta_segura(p):
    """MICA_RECOMENDACIONES_V2_5_A: sin exponer costos internos ni insumos."""
    if not p['dentro_presupuesto']:
        comentario = 'Supera el presupuesto indicado. Puedes ajustar el monto o consultar otras preparaciones.'
    elif p['requiere_compra']:
        comentario = 'Se ajusta al presupuesto, pero algunos insumos requieren reposición antes de confirmar.'
    else:
        comentario = 'Se ajusta al presupuesto y tiene disponibilidad estimada de ingredientes. Requiere confirmación del personal.'
    return {
        'id_ficha_tecnica': p['id_ficha_tecnica'], 'nombre': p['nombre'],
        'preparacion': p['preparacion'], 'descripcion': p.get('descripcion', ''),
        'comentario': comentario, 'personas': p['personas'],
        'precio_total': p['precio_total'], 'precio_persona': p['precio_persona'],
        'dentro_presupuesto': p['dentro_presupuesto'],
        'requiere_compra': p['requiere_compra'],
        'tipo_preparacion': p.get('tipo_preparacion', ''),
    }


@method_decorator(ensure_csrf_cookie, name='dispatch')
class MicaPublicoCatalogoView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        fichas = FichaTecnica.objects.filter(estado__iexact='activo').order_by('nombre_ficha')[:100]
        return Response({
            'preparaciones': [{'id': x.pk, 'nombre': x.nombre_ficha,
                               'descripcion': (x.descripcion or '')[:250],
                               'tipo_preparacion': x.tipo_preparacion or '',
                               'grupo': grupo_de(x.tipo_preparacion)} for x in fichas],
            'aviso': 'La propuesta es preliminar y requiere revisión humana antes de confirmar el pedido.',
        })


@method_decorator(csrf_protect, name='dispatch')
class MicaPublicoSimularView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'mica_publica_simular'

    def post(self, request):
        serializer = DatosEventoPublicoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            propuestas, descartadas, _, _, avisos = simular_publico(serializer.validated_data)
        except DjangoValidationError as exc:
            return Response({'detail': exc.messages}, status=422)
        # La IA genera texto explicativo, no precios ni decisiones automáticas.
        instancias = [SimpleNamespace(
            nombre=p['nombre'],
            detalle={'preparacion': p['preparacion'], 'descripcion': p.get('descripcion', '')},
            precio_total=p['precio_total'], dentro_presupuesto=p['dentro_presupuesto'],
            requiere_compra=p['requiere_compra'],
        ) for p in propuestas]
        contexto = {'tipo_evento': serializer.validated_data['tipo_evento'],
                    'personas': serializer.validated_data['personas']}
        explicacion = explicar(instancias, contexto=contexto) if propuestas else {
            'modo': 'reglas', 'mensaje': 'No hay preparaciones válidas para esos datos. Consulte al personal.',
            'proveedor_activo': False}
        return Response({
            'propuestas': [propuesta_segura(p) for p in propuestas],
            'descartadas': len(descartadas), 'avisos': avisos,
            'explicacion': {'modo': explicacion['modo'], 'mensaje': explicacion['mensaje'],
                         'proveedor': explicacion.get('proveedor', 'reglas'),
                         'modelo': explicacion.get('modelo'),
                         'proveedor_activo': explicacion.get('proveedor_activo', False)},
        })


@method_decorator(csrf_protect, name='dispatch')
class MicaPublicoSolicitarView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'mica_publica_enviar'

    @transaction.atomic
    def post(self, request):
        serializer = EnviarSolicitudPublicaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        datos = serializer.validated_data
        if datos.get('identificador'):
            existente = CotizacionMica.objects.filter(identificador=datos['identificador'], origen='publico').first()
            if existente:
                return Response({'cotizacion_id': existente.pk, 'pedido_id': existente.pedido_id,
                                 'numero_pedido': existente.pedido.numero_pedido, 'estado': 'CREADO',
                                 'mensaje': 'La solicitud ya estaba registrada. No se duplicó.'})
        try:
            propuestas, _, margen, costos, avisos = simular_publico(datos)
        except DjangoValidationError as exc:
            return Response({'detail': exc.messages}, status=422)
        seleccion = next((p for p in propuestas if p['id_ficha_tecnica'] == datos['ficha_id']), None)
        if seleccion is None:
            return Response({'ficha_id': 'Preparación no disponible; vuelva a simular.'}, status=409)
        if not seleccion['dentro_presupuesto']:
            return Response({'detail': 'La propuesta excede el presupuesto. Vuelva a simular.'}, status=409)
        if dinero(datos['precio_mostrado']) != dinero(seleccion['precio_total']):
            return Response({'detail': 'El precio cambió desde la simulación. Actualice las alternativas antes de enviar.'}, status=409)
        estado = EstadoPedido.objects.filter(nombre_estado__iexact='CREADO').first()
        if not estado:
            return Response({'detail': 'No existe estado CREADO; solicite al personal configurar el catálogo.'}, status=503)
        with connection.cursor() as cursor:
            cursor.execute("SELECT nextval('public.pedido_numero_seq')")
            numero = int(cursor.fetchone()[0])
        ahora = timezone.now()
        cliente = Cliente.objects.create(
            tipo_cliente='persona_natural', nombre=datos['nombre'], apellido=datos['apellido'],
            email=datos['email'], telefono=datos['telefono'], direccion=datos['ubicacion'],
            estado='activo',
        )
        evento = Evento.objects.create(
            nombre_evento=datos['tipo_evento'], fecha_evento=datos['fecha'],
            direccion=datos['ubicacion'], cantidad_personas=datos['personas'],
            observaciones=(datos.get('comentario') or '')[:1500], estado='pendiente_revision',
            id_cliente=cliente, created_at=ahora, updated_at=ahora,
        )
        cotizacion = CotizacionMica.objects.create(
            cliente=cliente, evento=evento, personas=datos['personas'],
            presupuesto=datos['presupuesto'], margen=margen,
            costo_personal=costos['costo_personal'], costo_transporte=costos['costo_transporte'],
            otros_costos=costos['otros_costos'],
            requisitos={'fecha': datos['fecha'].isoformat(), 'ubicacion': datos['ubicacion'],
                        'tipo_evento': datos['tipo_evento'],
                        'grupo': datos.get('grupo', ''),
                        'tipo_preparacion': datos.get('tipo_preparacion', ''),
                        'comentario': datos.get('comentario', ''),
                        'restricciones': [], 'advertencias': avisos},
            origen='publico', estado='pendiente_revision', creada_por=None,
            identificador=datos.get('identificador') or uuid4(),
        )
        for propuesta in propuestas:
            guardada = PropuestaMica.objects.create(
                cotizacion=cotizacion, nombre=propuesta['nombre'], ficha_id=propuesta['id_ficha_tecnica'],
                detalle=propuesta, costo_total=Decimal(propuesta['costo_total']),
                precio_total=Decimal(propuesta['precio_total']), precio_persona=Decimal(propuesta['precio_persona']),
                dentro_presupuesto=propuesta['dentro_presupuesto'], requiere_compra=propuesta['requiere_compra'],
            )
            if propuesta['id_ficha_tecnica'] == seleccion['id_ficha_tecnica']:
                cotizacion.propuesta_aceptada = guardada.pk
        pedido = Pedido.objects.create(
            numero_pedido=f'PED-{numero:06d}', id_cliente=cliente, id_evento=evento,
            fecha_entrega=datos['fecha'], id_estado_pedido=estado,
            costo_estimado=Decimal(seleccion['costo_total']),
            margen_objetivo=margen, precio_estimado=Decimal(seleccion['precio_total']),
            observaciones=f'Solicitud web MICA #{cotizacion.pk}. PENDIENTE DE REVISIÓN. '
                          f'Alternativa: {seleccion["preparacion"]}. '
                          f'Stock por validar. {datos.get("comentario", "")}'[:1900],
        )
        # El subtotal de detalle_pedido es GENERATED ALWAYS: no escribirlo.
        with connection.cursor() as cursor:
            cursor.execute(
                '''INSERT INTO detalle_pedido
                (id_pedido, tipo_detalle, id_ficha_tecnica, descripcion_manual, cantidad, costo_unitario, precio_unitario)
                VALUES (%s, %s, %s, %s, %s, %s, %s)''',
                [pedido.pk, 'ficha_tecnica', seleccion['id_ficha_tecnica'],
                 f'Solicitud web MICA #{cotizacion.pk} — {datos["personas"]} comensales',
                 Decimal('1'), Decimal(seleccion['costo_total']), Decimal(seleccion['precio_total'])]
            )
        HistorialPedido.objects.create(
            id_pedido=pedido, id_estado_anterior=None, id_estado_nuevo=estado,
            observacion='Solicitud web MICA recibida. Pendiente de revisión y aprobación humana.',
            id_usuario=None, fecha_cambio=ahora,
        )
        cotizacion.pedido = pedido
        cotizacion.save(update_fields=['pedido', 'propuesta_aceptada'])
        return Response({
            'cotizacion_id': cotizacion.pk, 'pedido_id': pedido.pk,
            'numero_pedido': pedido.numero_pedido, 'estado': 'CREADO',
            'precio_estimado': str(pedido.precio_estimado),
            'mensaje': 'Solicitud recibida. El pedido está pendiente de revisión; aún no se ha confirmado el evento.',
        }, status=status.HTTP_201_CREATED)


class RevisionPublicaSerializer(serializers.Serializer):
    accion = serializers.ChoiceField(choices=['aprobar', 'rechazar'])
    nota = serializers.CharField(max_length=1000, required=False, allow_blank=True, default='')
    compra_confirmada = serializers.BooleanField(required=False, default=False)


class MicaRevisionPublicaView(APIView):
    permission_classes = [IsAdminUser]

    @transaction.atomic
    def post(self, request, pk):
        serializer = RevisionPublicaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        datos = serializer.validated_data
        cot = get_object_or_404(CotizacionMica.objects.select_for_update(), pk=pk, origen='publico')
        if cot.estado != 'pendiente_revision':
            return Response({'detail': 'La solicitud ya fue revisada.', 'estado': cot.estado}, status=409)
        propuesta = get_object_or_404(PropuestaMica, pk=cot.propuesta_aceptada, cotizacion=cot)
        if datos['accion'] == 'aprobar':
            nombre_estado, nuevo = 'CONFIRMADO', 'aprobada'
        else:
            nombre_estado, nuevo = 'RECHAZADO', 'rechazada'
        estado = EstadoPedido.objects.filter(nombre_estado__iexact=nombre_estado).first()
        if not estado:
            return Response({'detail': f'Falta el estado {nombre_estado} en estado_pedido.'}, status=503)
        pedido = Pedido.objects.select_for_update().get(pk=cot.pedido_id)
        anterior = pedido.id_estado_pedido
        if anterior.nombre_estado.upper() != 'CREADO':
            return Response({'detail': 'El pedido ya cambió de estado desde otro módulo; revise antes de continuar.'}, status=409)
        if datos['accion'] == 'aprobar':
            try:
                reservas_creadas = reservar_pedido(cot, propuesta, pedido)
            except ReservaError as exc:
                return Response({'detail': str(exc)}, status=409)
        else:
            reservas_creadas = 0
        pedido.id_estado_pedido = estado
        pedido.save(update_fields=['id_estado_pedido', 'updated_at'])
        if cot.evento_id:
            Evento.objects.filter(pk=cot.evento_id).update(estado='confirmado' if nuevo == 'aprobada' else 'rechazado')
        cot.estado = nuevo
        cot.revisada_por = request.user
        cot.revisada_en = timezone.now()
        cot.nota_revision = datos['nota']
        cot.aceptada_en = cot.revisada_en if nuevo == 'aprobada' else None
        cot.save(update_fields=['estado', 'revisada_por', 'revisada_en', 'nota_revision', 'aceptada_en'])
        usuario = Usuario.objects.filter(email=request.user.email).first() if request.user.email else None
        HistorialPedido.objects.create(
            id_pedido=pedido, id_estado_anterior=anterior, id_estado_nuevo=estado,
            observacion=f'MICA — {datos["accion"]}. {datos["nota"]}'[:1000],
            id_usuario=usuario, fecha_cambio=timezone.now(),
        )
        return Response({'pedido_id': pedido.pk, 'numero_pedido': pedido.numero_pedido, 'estado': nuevo, 'reservas_creadas': reservas_creadas})


# MICA_RESERVAS_V2_3: cancelación de pedido confirmado, libera la reserva sin descontar inventario.
class MicaCancelarConfirmadoView(APIView):
    permission_classes = [IsAdminUser]

    @transaction.atomic
    def post(self, request, pk):
        cot = get_object_or_404(CotizacionMica.objects.select_for_update(), pk=pk, origen='publico')
        if cot.estado != 'aprobada' or not cot.pedido_id:
            return Response({'detail': 'Solo se cancelan pedidos públicos aprobados aún no preparados.'}, status=409)
        pedido = Pedido.objects.select_for_update().select_related('id_estado_pedido').get(pk=cot.pedido_id)
        if pedido.id_estado_pedido.nombre_estado.upper() != 'CONFIRMADO':
            return Response({'detail': 'No se puede cancelar desde MICA un pedido en preparación u otro estado.'}, status=409)
        reservas = ReservaInsumoMica.objects.select_for_update().filter(pedido=pedido, estado='reservada')
        if not reservas.exists():
            return Response({'detail': 'No existen reservas activas para liberar. Requiere revisión manual.'}, status=409)
        estado = EstadoPedido.objects.filter(nombre_estado__iexact='CANCELADO').first()
        if not estado:
            return Response({'detail': 'No existe estado CANCELADO.'}, status=503)
        anterior = pedido.id_estado_pedido
        liberadas = liberar_reservas(pedido)
        pedido.id_estado_pedido = estado
        pedido.save(update_fields=['id_estado_pedido', 'updated_at'])
        if cot.evento_id:
            Evento.objects.filter(pk=cot.evento_id).update(estado='cancelado')
        cot.estado = 'cancelada'
        cot.nota_revision = ('Cancelado por personal. ' + str(request.data.get('nota') or ''))[:1000]
        cot.revisada_en = timezone.now()
        cot.revisada_por = request.user
        cot.save(update_fields=['estado', 'nota_revision', 'revisada_en', 'revisada_por'])
        usuario = Usuario.objects.filter(email=request.user.email).first() if request.user.email else None
        HistorialPedido.objects.create(
            id_pedido=pedido, id_estado_anterior=anterior, id_estado_nuevo=estado,
            observacion=f'MICA: cancelación con {liberadas} reservas liberadas.',
            id_usuario=usuario, fecha_cambio=timezone.now(),
        )
        return Response({'pedido_id': pedido.pk, 'numero_pedido': pedido.numero_pedido,
                         'estado': 'cancelada', 'reservas_liberadas': liberadas})
