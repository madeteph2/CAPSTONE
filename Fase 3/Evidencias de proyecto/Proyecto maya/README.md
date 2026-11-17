# Banquetería Maya — Versión de integración MICA

Basada en el ZIP `Proyecto_Banqueteria(v1).zip`, sin modificar el original.

## Inicio

Lea primero **GUIA_EJECUCION_MICA.md**. Necesitará Python 3.12, Node.js compatible con Vite 8, PostgreSQL y VS Code. La carpeta **no incluye** `.venv`, `node_modules` ni secretos; se instalan localmente.

- Django + DRF: backend con autenticación mediante sesión y protección CSRF.
- React + Vite: frontend web, incluye pantalla MICA.
- PostgreSQL: 31 tablas heredadas + 2 tablas nuevas de MICA (migraciones).
- IA: opcional; sin clave funciona el cálculo determinista y las explicaciones de respaldo.

**Seguridad:** los scripts SQL de instalación solo deben ejecutarse en una base NUEVA y VACÍA. No tocar `sig_banqueteria` ni `sig_banqueteria_seba`.

## Estado comprobado (desde el entorno de preparación)

- `manage.py check` con SQLite de verificación: correcto.
- `makemigrations --check --dry-run`: sin cambios.
- Seis pruebas unitarias del motor: correctas.
- Prueba de API con esquema SQLite temporal: simulación, guardado, consulta, permisos, fallback IA y aceptación sin duplicación, correcta (no equivale a PostgreSQL).
- No se pudo ejecutar integración completa con PostgreSQL ni compilar Vite en Linux: el ZIP original traía módulos nativos de Windows, y este entorno no ofrece los paquetes de Linux.
- **La entrega es una versión candidata para pruebas en Windows, NO una certificación de funcionamiento integral.**

## Alcance de MICA

- Simulación y guardado de alternativas **por preparación** usando fichas, recetas e insumos activos.
- Cálculos en Django con `Decimal`, validación de margen mínimo y conversión kg/g/l/ml/unidades.
- Presupuestos insuficientes, stock consultado, advertencias de faltantes.
- Cotización independiente de pedido y guardado de líneas de ingredientes y costos como snapshot JSON.
- Aceptación en transacción atómica que genera pedido y detalle (previa validación y confirmación de compras pendientes).
- Asistente Groq opcional si existe cuenta gratuita habilitada (cuotas no garantizadas); explicación local por reglas si no hay proveedor.
- Consulta por código QR para lector futuro: `GET /api/mica/qr/insumos/<codigo>/` (no incluye escáner ni aplicación Android).

## Pendientes reconocidos

- Catálogo de alérgenos validado, reglas de contaminación cruzada y restricciones dietarias automáticas. MICA las rechaza de manera segura por ahora.
- Menús multi-preparación, servicios personalizados y cálculo de impuestos no están implementados en el motor nuevo.
- Dashboard financiero, flujos completos de ventas/facturación interna, permisos granulares y app Android/QR siguen incompletos en la versión heredada.
- La integración de todo el frontend y SQL requiere pruebas manuales en Windows/PostgreSQL.

Los endpoints MICA aceptan solo cuentas **staff** de Django. Los costos quedan restringidos a personal administrativo; aún debe implementarse un perfil comercial de cliente separado.
