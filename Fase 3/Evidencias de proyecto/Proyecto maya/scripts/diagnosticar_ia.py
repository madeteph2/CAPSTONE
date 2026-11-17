"""Prueba real opcional de comunicación IA de MICA; no consulta PostgreSQL."""
from pathlib import Path
from types import SimpleNamespace
from dotenv import load_dotenv

BASE = Path(__file__).resolve().parent.parent
load_dotenv(BASE / '.env', override=True)

from mica.ai import explicar


if __name__ == '__main__':
    propuesta = SimpleNamespace(
        nombre='Menú de demostración',
        detalle={'preparacion': 'Pollo con puré'},
        precio_total='150000',
        dentro_presupuesto=True,
    )
    resultado = explicar([propuesta])
    print('=== DIAGNÓSTICO DE IA MICA ===')
    print('Modo:', resultado['modo'])
    print('Proveedor:', resultado['proveedor'])
    print('Modelo:', resultado['modelo'])
    print('IA activa:', resultado['proveedor_activo'])
    print('Respuesta:', resultado['mensaje'])
