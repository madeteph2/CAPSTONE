"""Administración autenticada de paquetes comerciales MICA.

MICA v2.5B2-Admin: catálogo exclusivamente; NO simula ni reserva paquetes.
El contrato usa ids de fichas y cantidades de productos terminados por comensal.
"""
from decimal import Decimal
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from rest_framework import serializers, status
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from gestion.models import FichaTecnica
from .models import PaqueteMica, ComponentePaqueteMica


class ComponenteEntradaSerializer(serializers.Serializer):
    id_ficha_tecnica = serializers.IntegerField(min_value=1)
    cantidad_por_persona = serializers.DecimalField(
        max_digits=9, decimal_places=3, min_value=Decimal('0.001')
    )


class PaqueteEntradaSerializer(serializers.Serializer):
    nombre = serializers.CharField(max_length=150, trim_whitespace=True, allow_blank=False)
    tipo_servicio = serializers.ChoiceField(choices=PaqueteMica.TIPOS)
    descripcion = serializers.CharField(max_length=2000, allow_blank=True, default='')
    componentes = ComponenteEntradaSerializer(many=True, allow_empty=False)

    def validate_componentes(self, componentes):
        if len(componentes) > 30:
            raise serializers.ValidationError('Un paquete admite como máximo 30 preparaciones.')
        ids = [x['id_ficha_tecnica'] for x in componentes]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError('No repita una ficha. Ajuste su cantidad por persona.')
        return componentes


def validar_fichas(componentes):
    ids = [x['id_ficha_tecnica'] for x in componentes]
    fichas = FichaTecnica.objects.filter(pk__in=ids, estado__iexact='activo')
    encontrados = set(fichas.values_list('pk', flat=True))
    faltan = sorted(set(ids) - encontrados)
    if faltan:
        raise serializers.ValidationError({
            'componentes': f'Fichas inexistentes o inactivas: {faltan}.'
        })


def paquete_publicable(p):
    return {
        'id': p.pk,
        'nombre': p.nombre,
        'tipo_servicio': p.tipo_servicio,
        'descripcion': p.descripcion,
        'activo': p.activo,
        'componentes': [
            {
                'id_ficha_tecnica': c.ficha_id,
                'nombre_ficha': c.ficha.nombre_ficha,
                'tipo_preparacion': c.ficha.tipo_preparacion,
                'cantidad_por_persona': str(c.cantidad_por_persona),
            }
            for c in p.componentes.all()
        ],
    }


def listado():
    return PaqueteMica.objects.prefetch_related('componentes__ficha').order_by('nombre', 'pk')


def guardar_componentes(paquete, componentes):
    # La validación ocurre antes de borrar; todo dentro de transaction.atomic.
    ComponentePaqueteMica.objects.filter(paquete=paquete).delete()
    ComponentePaqueteMica.objects.bulk_create([
        ComponentePaqueteMica(
            paquete=paquete,
            ficha_id=x['id_ficha_tecnica'],
            cantidad_por_persona=x['cantidad_por_persona'],
            orden=i + 1,
        )
        for i, x in enumerate(componentes)
    ])


def validar_nombre_unico(nombre, tipo, omitir=None):
    existentes = PaqueteMica.objects.filter(nombre__iexact=nombre, tipo_servicio=tipo)
    if omitir is not None:
        existentes = existentes.exclude(pk=omitir)
    if existentes.exists():
        raise serializers.ValidationError({
            'nombre': 'Ya existe un paquete con este nombre y tipo de servicio.'
        })


class PaquetesListaCrearView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        return Response({'paquetes': [paquete_publicable(p) for p in listado()]})

    @transaction.atomic
    def post(self, request):
        entrada = PaqueteEntradaSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        d = entrada.validated_data
        validar_fichas(d['componentes'])
        validar_nombre_unico(d['nombre'], d['tipo_servicio'])
        try:
            paquete = PaqueteMica.objects.create(
                nombre=d['nombre'], tipo_servicio=d['tipo_servicio'],
                descripcion=d['descripcion'], activo=True,
            )
            guardar_componentes(paquete, d['componentes'])
        except IntegrityError:
            raise serializers.ValidationError({'detail': 'Paquete duplicado o datos no válidos.'})
        return Response(paquete_publicable(listado().get(pk=paquete.pk)), status=status.HTTP_201_CREATED)


class PaquetesDetalleView(APIView):
    permission_classes = [IsAdminUser]

    def put(self, request, pk):
        entrada = PaqueteEntradaSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        d = entrada.validated_data
        with transaction.atomic():
            paquete = get_object_or_404(PaqueteMica.objects.select_for_update(), pk=pk)
            validar_fichas(d['componentes'])
            validar_nombre_unico(d['nombre'], d['tipo_servicio'], omitir=pk)
            paquete.nombre = d['nombre']
            paquete.tipo_servicio = d['tipo_servicio']
            paquete.descripcion = d['descripcion']
            try:
                paquete.save(update_fields=['nombre', 'tipo_servicio', 'descripcion', 'actualizado_en'])
                guardar_componentes(paquete, d['componentes'])
            except IntegrityError:
                raise serializers.ValidationError({'detail': 'Paquete duplicado o datos no válidos.'})
        return Response(paquete_publicable(listado().get(pk=pk)))

    def patch(self, request, pk):
        if set(request.data.keys()) != {'activo'} or not isinstance(request.data['activo'], bool):
            raise serializers.ValidationError({'activo': 'Envíe exclusivamente true o false.'})
        with transaction.atomic():
            paquete = get_object_or_404(PaqueteMica.objects.select_for_update(), pk=pk)
            if request.data['activo']:
                validar_fichas([
                    {'id_ficha_tecnica': x} for x in
                    paquete.componentes.values_list('ficha_id', flat=True)
                ])
            paquete.activo = request.data['activo']
            paquete.save(update_fields=['activo', 'actualizado_en'])
        return Response(paquete_publicable(listado().get(pk=pk)))
