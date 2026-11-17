from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("gestion", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                ALTER TABLE ficha_tecnica
                ADD COLUMN IF NOT EXISTS procedimiento TEXT;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]