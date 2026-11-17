from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('mica', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='cotizacionmica', name='creada_por',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='cotizacionmica', name='estado',
            field=models.CharField(max_length=24, default='borrador', choices=[('borrador', 'Borrador interno'), ('aceptada', 'Aceptada internamente'), ('pendiente_revision', 'Pendiente de revisión'), ('aprobada', 'Aprobada'), ('rechazada', 'Rechazada')]),
        ),
        migrations.AddField(
            model_name='cotizacionmica', name='origen',
            field=models.CharField(max_length=12, default='interno', choices=[('interno', 'Interno'), ('publico', 'Consumidor')]),
        ),
        migrations.AddField(
            model_name='cotizacionmica', name='identificador', field=models.UUIDField(blank=True, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='cotizacionmica', name='nota_revision', field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='cotizacionmica', name='revisada_por',
            field=models.ForeignKey(blank=True, null=True, related_name='cotizaciones_mica_revisadas', on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='cotizacionmica', name='revisada_en', field=models.DateTimeField(blank=True, null=True),
        ),
    ]
