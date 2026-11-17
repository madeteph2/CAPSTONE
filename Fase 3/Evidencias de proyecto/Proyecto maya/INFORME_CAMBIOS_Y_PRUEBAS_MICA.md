# INFORME DE CAMBIOS Y VERIFICACIONES — MICA
**Fecha:** 10 de noviembre de 2026. **Origen:** Proyecto_Banqueteria(v1).zip. **Estado:** candidata de integración académica, NO despliegue validado.

## Decisiones de arquitectura

- Se conserva Django 6.1.2, DRF 3.18.3, PostgreSQL y React/Vite; no se cambió a FastAPI, JWT ni otro stack.
- Nueva aplicación Django `mica` independiente: el esquema original de `gestion` permanece como tablas heredadas `managed=False`.
- Dos nuevas tablas con migración `mica.0001_initial`: `mica_cotizacionmica` y `mica_propuestamica`, con relaciones a cliente, evento, pedido y ficha técnica.
- Se utiliza una **base nueva** `sig_banqueteria_mica`. Los SQL iniciales de la v1 con `DROP TABLE` no se incluyen en el paquete final.
- La IA es opcional (Groq solo con credenciales personales y cuota disponible). Sin Groq, cálculo automático y explicación por reglas.

## Funciones incorporadas

1. API `POST /api/mica/simular/`: validación y cálculo de alternativas desde fichas/recetas/insumos reales, personas, servicios, margen y presupuesto.
2. API `GET/POST /api/mica/cotizaciones/`: lectura de hasta 100 cotizaciones y persistencia de snapshots inmutables de insumos/costos/condiciones.
3. API `GET /api/mica/cotizaciones/<id>/`: consulta de detalle según permisos.
4. API `POST /api/mica/cotizaciones/<id>/aceptar/`: registro transaccional y único de pedido, con rechazo si excede presupuesto o si no se reconocen faltantes de stock.
5. API `POST /api/mica/cotizaciones/<id>/explicar/`: explicación por reglas o Groq (sin enviar datos personales del cliente).
6. API `GET /api/mica/qr/insumos/<codigo>/`: lectura de artículo por código QR existente, como contrato futuro; no incluye cámara ni app móvil.
7. `frontend/src/MicaVista.jsx`: reemplaza la lógica visual del antiguo cotizador v1 e interactúa con la API nueva.
8. Corrección de conversión de decimales al reabrir formularios de receta/rendimiento en React; cantidades de receta admiten tres decimales.
9. El backend recalcula costos de receta desde el costo vigente del insumo y las unidades; sincroniza costo total de ficha ante altas, cambios y bajas de ingredientes.
10. El cotizador legado de `gestion` queda de **solo lectura**, evitando aceptar totales enviados directamente por el cliente.
11. La modificación de cliente en Eventos bloquea cambios incompatibles con pedidos vinculados.
12. Configuración de claves/DB por variables `.env`; `ALLOWED_HOSTS` limitado a localhost. Archivos de entorno excluidos del ZIP.
13. Secuencia `pedido_numero_seq` creada en SQL seguro, evitando el error de alta de pedidos de la v1.

## Verificaciones ejecutadas

| Verificación | Resultado | Límite |
|---|---|---|
| Comprobación `python manage.py check` usando el Django del ZIP original | OK, 0 issues | Modo SQLite temporal |
| `makemigrations --check --dry-run` | Sin cambios pendientes | No verifica PostgreSQL |
| 6 pruebas de `mica.tests.test_motor` | 6/6 OK | Reglas aritméticas y conversiones |
| Parseo TS/JSX de `App.jsx` y `MicaVista.jsx` | Sin errores sintácticos | No equivale a `npm run build` ni prueba visual |
| SQLite temporal (migración MICA) | Aplicada `mica.0001_initial` | La migración legacy `gestion.0002` se marcó fake SOLO para este laboratorio porque contiene SQL específico de PostgreSQL |
| API de MICA con BD de laboratorio SQLite | Simular 200, guardar 201, detalle 200, explicación por reglas 200, restricciones 400, no admin 403 | No sustituye la integración con PostgreSQL |
| Aceptación de propuesta y reintento | Primera 201 y segunda 409; solo 1 pedido | La secuencia `nextval` fue simulada por SQLite; ejecutar prueba real en PostgreSQL |
| Compilación Vite | No verificable en este entorno | El ZIP v1 contiene binarios Windows; faltan binarios nativos Linux y no hay acceso a npm para descargarlos |
| Ejecución PostgreSQL real + navegador Windows | **Pendiente** | Debe hacerse en el computador de entrega |

## Límites y riesgos abiertos

- MICA genera **alternativas de una preparación por cotización**, no menús completos combinados con entrada, fondo y postre. Esa función queda para una iteración posterior.
- Los costos laborales/transporte/otros se introducen manualmente; se validan matemáticamente en el backend, pero aún no hay catálogo de tarifas. Se deben declarar explícitos, no asumir importes.
- Las existencias se consultan, no se reservan. Es necesaria confirmación de compra o reposición si falta stock.
- Las restricciones alimentarias se rechazan hasta contar con catálogo de alérgenos validado y revisión humana.
- IVA e impuestos no se aplican ni se calculan automáticamente; se requiere definición comercial/tributaria.
- Hay 2 fichas demo en el SQL; no siempre se generarán tres alternativas. No se deben inventar propuestas para llenar categorías.
- El motor inteligente **no entrena ni ejecuta un modelo local**: utiliza reglas y una API de IA opcional. No se incluye clave de proveedor.
- La app Android, cámara QR, permisos por rol detallados, dashboard financiero y flujos completos de ventas/auditoría de la v1 no están finalizados aquí.
- Es necesario revisar el frontend completo en Chrome y reproducir migraciones PostgreSQL antes de declarar el proyecto funcional integralmente.

## Próximas pruebas en el computador de desarrollo

1. Instalar todo en la base de pruebas nueva (guía de ejecución) y guardar salidas de `manage.py check` y `scripts/diagnosticar.py`.
2. Compilar Vite en Windows con `npm ci` y `npm run build`.
3. Probar creación de cliente, evento, ficha, receta y movimiento de inventario con una cuenta admin.
4. Simular, guardar y aceptar MICA con dos preparaciones y comprobar relaciones en pgAdmin.
5. Registrar fallos, corregirlos y repetir pruebas, sin modificar `sig_banqueteria` o `sig_banqueteria_seba`.

**Nota de alcance:** el documento de arranque original excluía IA; la ampliación debe aprobarse formalmente antes de registrarla como un compromiso académico completado.
