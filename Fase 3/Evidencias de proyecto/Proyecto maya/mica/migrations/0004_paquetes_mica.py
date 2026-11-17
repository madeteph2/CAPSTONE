# MICA v2.5B2 — solo estructura; no crea ni modifica cotizaciones históricas.
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('mica', '0003_reservainsumomica'),
        ('gestion', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PaqueteMica',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=150)),
                ('tipo_servicio', models.CharField(choices=[
                    ('coffee_break', 'Coffee break'),
                    ('coctel', 'Cóctel'),
                    ('almuerzo', 'Almuerzo'),
                    ('cena', 'Cena'),
                    ('banquete', 'Banquete'),
                    ('personalizado', 'Personalizado'),
                ], max_length=24)),
                ('descripcion', models.TextField(blank=True, default='')),
                ('activo', models.BooleanField(default=True)),
                ('creado_en', models.DateTimeField(auto_now_add=True)),
                ('actualizado_en', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['nombre', 'pk'],
            },
        ),
        migrations.CreateModel(
            name='ComponentePaqueteMica',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cantidad_por_persona', models.DecimalField(decimal_places=3, max_digits=9)),
                ('orden', models.PositiveSmallIntegerField(default=1)),
                ('ficha', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='componentes_mica', to='gestion.fichatecnica')),
                ('paquete', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='componentes', to='mica.paquetemica')),
            ],
            options={'ordering': ['orden', 'pk']},
        ),
        migrations.AlterField(
            model_name='propuestamica', name='ficha',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='gestion.fichatecnica'),
        ),
        migrations.AddField(
            model_name='propuestamica', name='paquete',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='propuestas_mica', to='mica.paquetemica'),
        ),
        migrations.AddConstraint(
            model_name='paquetemica',
            constraint=models.UniqueConstraint(fields=('tipo_servicio', 'nombre'), name='mica_paquete_tipo_nombre_unico'),
        ),
        migrations.AddConstraint(
            model_name='componentepaquetemica',
            constraint=models.UniqueConstraint(fields=('paquete', 'ficha'), name='mica_componente_paquete_ficha_unica'),
        ),
        migrations.AddConstraint(
            model_name='componentepaquetemica',
            constraint=models.CheckConstraint(condition=models.Q(cantidad_por_persona__gt=0), name='mica_componente_cantidad_positiva'),
        ),
        migrations.AddConstraint(
            model_name='propuestamica',
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(ficha__isnull=False, paquete__isnull=True)
                    | models.Q(ficha__isnull=True, paquete__isnull=False)
                ),
                name='mica_propuesta_ficha_xor_paquete',
            ),
        ),
    ]
