"""Diagnóstico no destructivo de PostgreSQL y tablas de Maya."""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
import django
django.setup()
from django.db import connection

NECESARIAS = ('cliente', 'evento', 'pedido', 'estado_pedido', 'ficha_tecnica',
              'receta', 'insumo', 'unidad', 'inventario', 'cotizacion',
              'mica_cotizacionmica', 'mica_propuestamica')

print('Base de datos configurada:', connection.settings_dict['NAME'])
try:
    with connection.cursor() as cursor:
        cursor.execute('SELECT current_database(), version()')
        db, version = cursor.fetchone()
        print('Conectado a:', db)
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
        actuales = {x[0] for x in cursor.fetchall()}
        print('Tablas esperadas:')
        for t in NECESARIAS:
            print('  [OK] ' if t in actuales else '  [FALTA] ', t)
        cursor.execute("SELECT to_regclass('public.pedido_numero_seq')")
        print('Secuencia pedidos:', cursor.fetchone()[0] or 'FALTA')
        if 'ficha_tecnica' in actuales and 'receta' in actuales:
            cursor.execute('SELECT count(*) FROM ficha_tecnica')
            print('Fichas:', cursor.fetchone()[0])
            cursor.execute('SELECT count(*) FROM receta')
            print('Recetas:', cursor.fetchone()[0])
except Exception as e:
    print('ERROR DE CONEXIÓN O ESQUEMA:', e.__class__.__name__, str(e))
    raise SystemExit(1)
