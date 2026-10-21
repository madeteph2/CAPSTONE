# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from django.utils import timezone


class Auditoria(models.Model):
    id_auditoria = models.AutoField(primary_key=True)
    id_usuario = models.ForeignKey('Usuario', models.DO_NOTHING, db_column='id_usuario', blank=True, null=True)
    modulo = models.CharField(max_length=80)
    accion = models.CharField(max_length=100)
    tabla_afectada = models.CharField(max_length=80, blank=True, null=True)
    id_registro_afectado = models.IntegerField(blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    fecha_hora = models.DateTimeField()
    ip_origen = models.CharField(max_length=60, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'auditoria'


class Bodega(models.Model):
    id_bodega = models.AutoField(primary_key=True)
    nombre_bodega = models.CharField(max_length=150)
    direccion = models.TextField(blank=True, null=True)
    tipo_bodega = models.CharField(max_length=60, blank=True, null=True)
    estado = models.CharField(max_length=20)

    class Meta:
        managed = False
        db_table = 'bodega'


class ChecklistMontaje(models.Model):
    id_checklist = models.AutoField(primary_key=True)
    id_pedido = models.ForeignKey('Pedido', models.CASCADE, db_column='id_pedido')
    item = models.CharField(max_length=200)
    estado = models.CharField(max_length=30)
    observaciones = models.TextField(blank=True, null=True)
    id_usuario = models.ForeignKey('Usuario', models.DO_NOTHING, db_column='id_usuario', blank=True, null=True)
    fecha_actualizacion = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'checklist_montaje'


class Cliente(models.Model):
    id_cliente = models.AutoField(primary_key=True)
    rut = models.CharField(max_length=20, blank=True, null=True)
    tipo_cliente = models.CharField(max_length=40)
    nombre = models.CharField(max_length=150)
    apellido = models.CharField(max_length=100, blank=True, null=True)
    nombre_fantasia = models.CharField(max_length=150, blank=True, null=True)
    giro = models.CharField(max_length=200, blank=True, null=True)
    email = models.CharField(max_length=150, blank=True, null=True)
    telefono = models.CharField(max_length=30, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    id_comuna = models.ForeignKey('Comuna', models.DO_NOTHING, db_column='id_comuna', blank=True, null=True)
    id_pais = models.ForeignKey('Pais', models.DO_NOTHING, db_column='id_pais', blank=True, null=True)
    id_representante_legal = models.ForeignKey('RepresentanteLegal', models.DO_NOTHING, db_column='id_representante_legal', blank=True, null=True)
    estado = models.CharField(max_length=20)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'cliente'


class Comuna(models.Model):
    id_comuna = models.IntegerField(primary_key=True)
    nombre_comuna = models.CharField(max_length=80)
    id_region = models.ForeignKey('Region', models.DO_NOTHING, db_column='id_region')

    class Meta:
        managed = False
        db_table = 'comuna'
        unique_together = (('nombre_comuna', 'id_region'),)


class Cotizacion(models.Model):
    id_cotizacion = models.AutoField(primary_key=True)
    id_pedido = models.ForeignKey('Pedido', models.CASCADE, db_column='id_pedido')
    fecha_cotizacion = models.DateTimeField()
    costo_insumos = models.DecimalField(max_digits=12, decimal_places=2)
    costo_personal = models.DecimalField(max_digits=12, decimal_places=2)
    costo_transporte = models.DecimalField(max_digits=12, decimal_places=2)
    otros_costos = models.DecimalField(max_digits=12, decimal_places=2)
    costo_total = models.DecimalField(max_digits=12, decimal_places=2)
    margen_objetivo = models.DecimalField(max_digits=5, decimal_places=2)
    precio_sugerido = models.DecimalField(max_digits=12, decimal_places=2)
    estado = models.CharField(max_length=30)
    observacion = models.TextField(blank=True, null=True)
    id_usuario = models.ForeignKey('Usuario', models.DO_NOTHING, db_column='id_usuario', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'cotizacion'


class DetallePedido(models.Model):
    id_detalle_pedido = models.AutoField(primary_key=True)
    id_pedido = models.ForeignKey('Pedido', models.CASCADE, db_column='id_pedido')
    tipo_detalle = models.CharField(max_length=30)
    id_ficha_tecnica = models.ForeignKey('FichaTecnica', models.DO_NOTHING, db_column='id_ficha_tecnica', blank=True, null=True)
    id_insumo = models.ForeignKey('Insumo', models.DO_NOTHING, db_column='id_insumo', blank=True, null=True)
    descripcion_manual = models.CharField(max_length=200, blank=True, null=True)
    cantidad = models.DecimalField(max_digits=12, decimal_places=3)
    costo_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'detalle_pedido'


class DetallePreparacion(models.Model):
    id_detalle_preparacion = models.AutoField(primary_key=True)
    id_ficha_tecnica = models.ForeignKey('FichaTecnica', models.CASCADE, db_column='id_ficha_tecnica')
    orden = models.IntegerField()
    instruccion = models.TextField()

    class Meta:
        managed = False
        db_table = 'detalle_preparacion'


class EstadoPedido(models.Model):
    id_estado_pedido = models.IntegerField(primary_key=True)
    nombre_estado = models.CharField(unique=True, max_length=40)
    descripcion = models.TextField(blank=True, null=True)
    orden = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'estado_pedido'


class Evento(models.Model):
    id_evento = models.AutoField(primary_key=True)
    nombre_evento = models.CharField(max_length=150)
    fecha_evento = models.DateField()
    hora_evento = models.TimeField(blank=True, null=True)
    direccion = models.TextField()
    cantidad_personas = models.IntegerField(blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    estado = models.CharField(max_length=30)
    id_cliente = models.ForeignKey(Cliente, models.DO_NOTHING, db_column='id_cliente')
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'evento'


class Factura(models.Model):
    id_factura = models.AutoField(primary_key=True)
    id_venta = models.ForeignKey('Venta', models.CASCADE, db_column='id_venta')
    numero_factura = models.CharField(max_length=50, blank=True, null=True)
    fecha_emision = models.DateField()
    monto_total = models.DecimalField(max_digits=12, decimal_places=2)
    estado = models.CharField(max_length=30)
    observacion = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'factura'


class FichaTecnica(models.Model):
    id_ficha_tecnica = models.AutoField(primary_key=True)
    nombre_ficha = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True, null=True)
    tipo_preparacion = models.CharField(max_length=80, blank=True, null=True)
    rendimiento = models.DecimalField(max_digits=12, decimal_places=3)
    id_unidad_rendimiento = models.ForeignKey('Unidad', models.DO_NOTHING, db_column='id_unidad_rendimiento', blank=True, null=True)
    costo_total = models.DecimalField(max_digits=12, decimal_places=2)
    precio_sugerido = models.DecimalField(max_digits=12, decimal_places=2)
    margen_objetivo = models.DecimalField(max_digits=5, decimal_places=2)
    imagen_url = models.TextField(blank=True, null=True)
    estado = models.CharField(max_length=20)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'ficha_tecnica'


class HistorialPedido(models.Model):
    id_historial_pedido = models.AutoField(primary_key=True)
    id_pedido = models.ForeignKey('Pedido', models.CASCADE, db_column='id_pedido')
    id_estado_anterior = models.ForeignKey(EstadoPedido, models.DO_NOTHING, db_column='id_estado_anterior', blank=True, null=True)
    id_estado_nuevo = models.ForeignKey(EstadoPedido, models.DO_NOTHING, db_column='id_estado_nuevo', related_name='historialpedido_id_estado_nuevo_set')
    observacion = models.TextField(blank=True, null=True)
    id_usuario = models.ForeignKey('Usuario', models.DO_NOTHING, db_column='id_usuario', blank=True, null=True)
    fecha_cambio = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'historial_pedido'


class Incidencia(models.Model):
    id_incidencia = models.AutoField(primary_key=True)
    id_pedido = models.ForeignKey('Pedido', models.CASCADE, db_column='id_pedido')
    id_usuario = models.ForeignKey('Usuario', models.DO_NOTHING, db_column='id_usuario', blank=True, null=True)
    descripcion = models.TextField()
    foto_url = models.TextField(blank=True, null=True)
    estado = models.CharField(max_length=30)
    fecha = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'incidencia'


class Insumo(models.Model):
    id_insumo = models.AutoField(primary_key=True)
    nombre_insumo = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True, null=True)
    categoria = models.CharField(max_length=60, blank=True, null=True)
    id_unidad = models.ForeignKey('Unidad', models.DO_NOTHING, db_column='id_unidad')
    costo_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    stock_minimo = models.DecimalField(max_digits=12, decimal_places=3)
    codigo_qr = models.CharField(unique=True, max_length=120, blank=True, null=True)
    id_proveedor = models.ForeignKey('Proveedor', models.DO_NOTHING, db_column='id_proveedor', blank=True, null=True)
    estado = models.CharField(max_length=20)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'insumo'


class Inventario(models.Model):
    id_inventario = models.AutoField(primary_key=True)
    id_insumo = models.ForeignKey(Insumo, models.DO_NOTHING, db_column='id_insumo')
    id_bodega = models.ForeignKey(Bodega, models.DO_NOTHING, db_column='id_bodega')
    stock_actual = models.DecimalField(max_digits=12, decimal_places=3)
    stock_minimo = models.DecimalField(max_digits=12, decimal_places=3)
    ubicacion = models.CharField(max_length=150, blank=True, null=True)
    estado = models.CharField(max_length=20)

    class Meta:
        managed = False
        db_table = 'inventario'
        unique_together = (('id_insumo', 'id_bodega'),)


class MovimientoInventario(models.Model):
    id_movimiento = models.AutoField(primary_key=True)
    tipo_movimiento = models.CharField(max_length=30)
    fecha_movimiento = models.DateTimeField()
    cantidad = models.DecimalField(max_digits=12, decimal_places=3)
    costo_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    observacion = models.TextField(blank=True, null=True)
    id_insumo = models.ForeignKey(Insumo, models.DO_NOTHING, db_column='id_insumo')
    id_bodega = models.ForeignKey(Bodega, models.DO_NOTHING, db_column='id_bodega')
    id_pedido = models.ForeignKey('Pedido', models.DO_NOTHING, db_column='id_pedido', blank=True, null=True)
    id_usuario = models.ForeignKey('Usuario', models.DO_NOTHING, db_column='id_usuario', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'movimiento_inventario'


class Pago(models.Model):
    id_pago = models.AutoField(primary_key=True)
    id_factura = models.ForeignKey(Factura, models.CASCADE, db_column='id_factura')
    fecha_pago = models.DateField()
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    metodo_pago = models.CharField(max_length=50, blank=True, null=True)
    estado = models.CharField(max_length=30)
    observacion = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'pago'


class Pais(models.Model):
    id_pais = models.IntegerField(primary_key=True)
    nombre_pais = models.CharField(unique=True, max_length=120)
    codigo_iso3 = models.CharField(unique=True, max_length=3)

    class Meta:
        managed = False
        db_table = 'pais'


class Parametro(models.Model):
    id_parametro = models.IntegerField(primary_key=True)
    nombre_parametro = models.CharField(unique=True, max_length=60)
    valor_numerico = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    valor_texto = models.CharField(max_length=200, blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    estado = models.CharField(max_length=20)

    class Meta:
        managed = False
        db_table = 'parametro'


class Pedido(models.Model):
    id_pedido = models.AutoField(primary_key=True)
    numero_pedido = models.CharField(unique=True, max_length=30)
    fecha_creacion = models.DateTimeField(default=timezone.now)
    fecha_compromiso = models.DateField(blank=True, null=True)
    fecha_entrega = models.DateField(blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    costo_estimado = models.DecimalField(max_digits=12, decimal_places=2)
    margen_objetivo = models.DecimalField(max_digits=5, decimal_places=2)
    precio_estimado = models.DecimalField(max_digits=12, decimal_places=2)
    id_cliente = models.ForeignKey(Cliente, models.DO_NOTHING, db_column='id_cliente')
    id_evento = models.ForeignKey(Evento, models.DO_NOTHING, db_column='id_evento', blank=True, null=True)
    id_estado_pedido = models.ForeignKey(EstadoPedido, models.DO_NOTHING, db_column='id_estado_pedido')
    id_usuario_responsable = models.ForeignKey('Usuario', models.DO_NOTHING, db_column='id_usuario_responsable', blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'pedido'


class Permiso(models.Model):
    id_permiso = models.AutoField(primary_key=True)
    nombre_permiso = models.CharField(unique=True, max_length=100)
    modulo = models.CharField(max_length=80)
    descripcion = models.TextField(blank=True, null=True)
    estado = models.CharField(max_length=20)

    class Meta:
        managed = False
        db_table = 'permiso'


class Proveedor(models.Model):
    id_proveedor = models.AutoField(primary_key=True)
    nombre_proveedor = models.CharField(max_length=150)
    rut = models.CharField(max_length=20, blank=True, null=True)
    nombre_contacto = models.CharField(max_length=100, blank=True, null=True)
    email = models.CharField(max_length=150, blank=True, null=True)
    telefono = models.CharField(max_length=30, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    id_comuna = models.ForeignKey(Comuna, models.DO_NOTHING, db_column='id_comuna', blank=True, null=True)
    id_pais = models.ForeignKey(Pais, models.DO_NOTHING, db_column='id_pais', blank=True, null=True)
    estado = models.CharField(max_length=20)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'proveedor'


class Receta(models.Model):
    id_receta = models.AutoField(primary_key=True)
    id_ficha_tecnica = models.ForeignKey(FichaTecnica, models.CASCADE, db_column='id_ficha_tecnica')
    id_insumo = models.ForeignKey(Insumo, models.DO_NOTHING, db_column='id_insumo')
    cantidad = models.DecimalField(max_digits=12, decimal_places=3)
    id_unidad = models.ForeignKey('Unidad', models.DO_NOTHING, db_column='id_unidad')
    costo_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    costo_total = models.DecimalField(max_digits=12, decimal_places=2)
    observacion = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'receta'
        unique_together = (('id_ficha_tecnica', 'id_insumo'),)


class Region(models.Model):
    id_region = models.IntegerField(primary_key=True)
    nombre_region = models.CharField(unique=True, max_length=100)

    class Meta:
        managed = False
        db_table = 'region'


class RepresentanteLegal(models.Model):
    id_representante_legal = models.AutoField(primary_key=True)
    rut = models.CharField(max_length=20, blank=True, null=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100, blank=True, null=True)
    email = models.CharField(max_length=150, blank=True, null=True)
    telefono = models.CharField(max_length=30, blank=True, null=True)
    estado = models.CharField(max_length=20)

    class Meta:
        managed = False
        db_table = 'representante_legal'


class Rol(models.Model):
    id_rol = models.AutoField(primary_key=True)
    nombre_rol = models.CharField(unique=True, max_length=80)
    descripcion = models.TextField(blank=True, null=True)
    estado = models.CharField(max_length=20)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'rol'


class RolPermiso(models.Model):
    pk = models.CompositePrimaryKey('id_rol', 'id_permiso')
    id_rol = models.ForeignKey(Rol, models.CASCADE, db_column='id_rol')
    id_permiso = models.ForeignKey(Permiso, models.CASCADE, db_column='id_permiso')

    class Meta:
        managed = False
        db_table = 'rol_permiso'


class Unidad(models.Model):
    id_unidad = models.IntegerField(primary_key=True)
    nombre_unidad = models.CharField(unique=True, max_length=30)

    class Meta:
        managed = False
        db_table = 'unidad'


class Usuario(models.Model):
    id_usuario = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100, blank=True, null=True)
    email = models.CharField(unique=True, max_length=150)
    password_hash = models.TextField()
    telefono = models.CharField(max_length=30, blank=True, null=True)
    estado = models.CharField(max_length=20)
    ultimo_acceso = models.DateTimeField(blank=True, null=True)
    id_rol = models.ForeignKey(Rol, models.DO_NOTHING, db_column='id_rol')
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'usuario'


class Venta(models.Model):
    id_venta = models.AutoField(primary_key=True)
    id_pedido = models.ForeignKey(Pedido, models.DO_NOTHING, db_column='id_pedido')
    fecha_venta = models.DateTimeField()
    total = models.DecimalField(max_digits=12, decimal_places=2)
    estado = models.CharField(max_length=30)
    observacion = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'venta'
