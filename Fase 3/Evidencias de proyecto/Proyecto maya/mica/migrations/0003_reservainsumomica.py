# MICA v2.3: reservas de materias primas sin descontar stock físico.
from django.db import migrations, models
import django.db.models.deletion
from django.db.models import Q
from django.utils import timezone


class Migration(migrations.Migration):
    dependencies = [
        ('mica', '0002_cotizacion_publica'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cotizacionmica', name='estado',
            field=models.CharField(max_length=24, default='borrador', choices=[
                ('borrador', 'Borrador interno'), ('aceptada', 'Aceptada internamente'),
                ('pendiente_revision', 'Pendiente de revisión'), ('aprobada', 'Aprobada'),
                ('rechazada', 'Rechazada'), ('cancelada', 'Cancelada')
            ]),
        ),
        migrations.CreateModel(
            name='ReservaInsumoMica',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cantidad', models.DecimalField(decimal_places=3, max_digits=12)),
                ('estado', models.CharField(max_length=12, choices=[('reservada', 'Reservada'), ('consumida', 'Consumida'), ('liberada', 'Liberada')], default='reservada')),
                ('creada_en', models.DateTimeField(default=timezone.now)),
                ('id_bodega', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='gestion.bodega')),
                ('id_insumo', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='gestion.insumo')),
                ('pedido', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='reservas_mica', to='gestion.pedido')),
            ],
        ),
        migrations.AddConstraint(
            model_name='reservainsumomica',
            constraint=models.UniqueConstraint(fields=['pedido', 'id_insumo', 'id_bodega'], name='mica_reserva_pedido_insumo_bodega_unica'),
        ),
        migrations.AddConstraint(
            model_name='reservainsumomica',
            constraint=models.CheckConstraint(condition=Q(cantidad__gt=0), name='mica_reserva_cantidad_positiva'),
        ),
    ]
