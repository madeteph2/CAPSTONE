"""MICA: tablas propias; no altera las tablas de negocio heredadas."""
from django.conf import settings
from django.db import models
from django.utils import timezone



class CotizacionMica(models.Model):
    ESTADOS = [
        ('borrador', 'Borrador interno'), ('aceptada', 'Aceptada internamente'),
        ('pendiente_revision', 'Pendiente de revisión'), ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada'), ('cancelada', 'Cancelada'),
    ]
    cliente = models.ForeignKey('gestion.Cliente', on_delete=models.PROTECT)
    evento = models.ForeignKey('gestion.Evento', on_delete=models.PROTECT, blank=True, null=True)
    pedido = models.OneToOneField('gestion.Pedido', on_delete=models.PROTECT, null=True, blank=True)
    personas = models.PositiveIntegerField()
    presupuesto = models.DecimalField(max_digits=14, decimal_places=2)
    margen = models.DecimalField(max_digits=5, decimal_places=2)
    costo_personal = models.DecimalField(max_digits=12, decimal_places=2)
    costo_transporte = models.DecimalField(max_digits=12, decimal_places=2)
    otros_costos = models.DecimalField(max_digits=12, decimal_places=2)
    requisitos = models.JSONField(default=dict)
    estado = models.CharField(max_length=24, choices=ESTADOS, default='borrador')
    origen = models.CharField(max_length=12, choices=[('interno', 'Interno'), ('publico', 'Consumidor')], default='interno')
    identificador = models.UUIDField(null=True, blank=True, unique=True)
    nota_revision = models.TextField(blank=True, default='')
    revisada_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name='cotizaciones_mica_revisadas')
    revisada_en = models.DateTimeField(null=True, blank=True)
    propuesta_aceptada = models.PositiveIntegerField(null=True, blank=True)
    creada_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True)
    creada_en = models.DateTimeField(auto_now_add=True)
    aceptada_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-creada_en']


class PropuestaMica(models.Model):
    cotizacion = models.ForeignKey(CotizacionMica, on_delete=models.CASCADE, related_name='propuestas')
    nombre = models.CharField(max_length=30)
    ficha = models.ForeignKey('gestion.FichaTecnica', on_delete=models.PROTECT, null=True, blank=True)
    paquete = models.ForeignKey('PaqueteMica', on_delete=models.PROTECT,
                                null=True, blank=True, related_name='propuestas_mica')
    # Copia inmutable de la oferta, incluidos costos, unidades y condiciones.
    detalle = models.JSONField()
    costo_total = models.DecimalField(max_digits=14, decimal_places=2)
    precio_total = models.DecimalField(max_digits=14, decimal_places=2)
    precio_persona = models.DecimalField(max_digits=14, decimal_places=2)
    dentro_presupuesto = models.BooleanField(default=False)
    requiere_compra = models.BooleanField(default=False)

    class Meta:
        ordering = ['precio_total', 'id']
        constraints = [
            models.CheckConstraint(
                condition=(models.Q(ficha__isnull=False, paquete__isnull=True)
                           | models.Q(ficha__isnull=True, paquete__isnull=False)),
                name='mica_propuesta_ficha_xor_paquete',
            ),
        ]


# MICA_RESERVAS_V2_3: compromisos de ingredientes sin descontar stock físico.
class ReservaInsumoMica(models.Model):
    ESTADOS = [('reservada', 'Reservada'), ('consumida', 'Consumida'), ('liberada', 'Liberada')]
    pedido = models.ForeignKey('gestion.Pedido', on_delete=models.PROTECT, related_name='reservas_mica')
    id_insumo = models.ForeignKey('gestion.Insumo', on_delete=models.PROTECT)
    id_bodega = models.ForeignKey('gestion.Bodega', on_delete=models.PROTECT)
    cantidad = models.DecimalField(max_digits=12, decimal_places=3)
    estado = models.CharField(max_length=12, choices=ESTADOS, default='reservada')
    creada_en = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['pedido', 'id_insumo', 'id_bodega'], name='mica_reserva_pedido_insumo_bodega_unica'),
            models.CheckConstraint(condition=models.Q(cantidad__gt=0), name='mica_reserva_cantidad_positiva'),
        ]


# MICA_PAQUETES_V2_5_B2_ESQUEMA
# Catálogo de paquetes; aún NO crea propuestas combinadas ni modifica reservas.
class PaqueteMica(models.Model):
    TIPOS = [
        ('coffee_break', 'Coffee break'),
        ('coctel', 'Cóctel'),
        ('almuerzo', 'Almuerzo'),
        ('cena', 'Cena'),
        ('banquete', 'Banquete'),
        ('personalizado', 'Personalizado'),
    ]
    nombre = models.CharField(max_length=150)
    tipo_servicio = models.CharField(max_length=24, choices=TIPOS)
    descripcion = models.TextField(default='', blank=True)
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nombre', 'pk']
        constraints = [
            models.UniqueConstraint(fields=['tipo_servicio', 'nombre'], name='mica_paquete_tipo_nombre_unico'),
        ]


class ComponentePaqueteMica(models.Model):
    paquete = models.ForeignKey(PaqueteMica, on_delete=models.CASCADE, related_name='componentes')
    ficha = models.ForeignKey('gestion.FichaTecnica', on_delete=models.PROTECT, related_name='componentes_mica')
    # Número de unidades terminadas de la ficha por invitado (no kg de insumo).
    cantidad_por_persona = models.DecimalField(max_digits=9, decimal_places=3)
    orden = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ['orden', 'pk']
        constraints = [
            models.UniqueConstraint(fields=['paquete', 'ficha'], name='mica_componente_paquete_ficha_unica'),
            models.CheckConstraint(condition=models.Q(cantidad_por_persona__gt=0), name='mica_componente_cantidad_positiva'),
        ]
