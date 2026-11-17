# GUÍA DE INSTALACIÓN Y EJECUCIÓN — BANQUETERÍA MAYA / MICA

**Versión de trabajo: 10 de noviembre de 2026 · Windows + VS Code + PostgreSQL.**

Esta entrega es una **candidata de integración** basada en la v1, no una instalación ya probada de punta a punta en tu computador. Sigue los pasos en orden y conserva los respaldos.

## 0. Qué contiene y qué NO contiene

La copia conserva Clientes, Eventos, Pedidos, Fichas/Recetas, Inventario y consultas de Ventas; incorpora MICA en la opción **Cotizador** de React. La app Android y el lector de cámara NO están implementados; se dejó un endpoint QR para integrarlos luego. El cotizador MICA usa fichas y recetas, propone una preparación por alternativa, calcula precios y permite aceptar un presupuesto para crear un pedido. Si no tienes clave de IA, funciona con reglas matemáticas y textos de respaldo; **no presenta eso como IA generativa**.

### Datos necesarios antes de probar

- Un servidor PostgreSQL operativo en el computador, con usuario y contraseña que conoces.
- Python 3.12.x y Node.js 24.x (o una versión que cumpla `vite@8`), npm y VS Code.
- Una **base nueva y vacía** llamada `sig_banqueteria_mica`. No renombres ni borres `sig_banqueteria` y `sig_banqueteria_seba`.
- Conexión a Internet solamente para instalar dependencias mediante `pip` y `npm`. No se exige servicio de IA para cotizar.

## 1. Respaldar antes de instalar

1. Conserva el ZIP **v1** y, preferiblemente, también la v2 hasta verificar esta copia.
2. En pgAdmin, comprueba el nombre de cada base antes de actuar. Utiliza **Backup...** sobre `sig_banqueteria` y `sig_banqueteria_seba` si deseas conservar sus datos.
3. No ejecutes `DROP DATABASE`, `DROP TABLE` ni los archivos SQL originales de v1 sobre las bases anteriores. El SQL original **del ZIP v1** contiene `DROP TABLE ... CASCADE` y deliberadamente no se incluyó en esta copia; usa solamente el nuevo SQL protegido de MICA.
4. Descomprime `MICA_Banqueteria_Proyecto.zip` en `C:\Capstone\`, de modo que exista `C:\Capstone\MICA_Banqueteria_Proyecto\manage.py`. Puede estar en otra ruta, pero ajusta los comandos.

## 2. Comprobar herramientas en PowerShell

Abre **Terminal → Nuevo terminal** en VS Code o PowerShell y ejecuta:

```powershell
py -0p
py -3.12 --version
node --version
npm.cmd --version
```

Si falla alguno, instala o repara esa herramienta y vuelve a abrir la terminal. Si `node` funciona pero npm no, revisa la instalación de Node.js.

## 3. Iniciar el servicio PostgreSQL

En PowerShell:

```powershell
Get-Service | Where-Object { $_.Name -like 'postgresql*' } | Select-Object Name,Status
```

Si aparece `Stopped`, inicia **el nombre exacto** que muestre tu equipo, desde una consola con permisos de administrador, por ejemplo:

```powershell
# EJEMPLO; cambia el nombre por el indicado en tu equipo
Start-Service -Name 'postgresql-x64-16'
```

Si ya dice `Running`, no necesitas hacer nada. También puedes entrar a pgAdmin 4 y confirmar que el servidor se conecta usando su contraseña.

**No hay un comando `activar base de datos` en Django:** PostgreSQL es un servicio. Primero lo enciendes; luego Django se conecta mediante `settings.py` y `.env`.

## 4. Crear una base de pruebas nueva, sin borrar las anteriores

1. Abre **pgAdmin 4**, conecta tu servidor local.
2. Clic derecho en **Databases → Create → Database...**.
3. Nombra la nueva base exactamente `sig_banqueteria_mica` y guarda.
4. **Selecciona esa nueva base**. Abre `Tools → Query Tool`.
5. Abre el archivo `database/01_INSTALACION_SOLO_BD_NUEVA.sql` en Query Tool y ejecútalo una sola vez, en esta base vacía.
6. Deberá crear las tablas y registros de demostración de v1, además de `pedido_numero_seq`. Si pgAdmin informa algún error, **detente y guarda el mensaje**. No repitas el script sobre una base parcialmente poblada.

Verificación en Query Tool (asegúrate de estar conectado a `sig_banqueteria_mica`):

```sql
SELECT current_database();
SELECT count(*) AS fichas FROM ficha_tecnica;
SELECT count(*) AS recetas FROM receta;
SELECT to_regclass('public.pedido_numero_seq') AS secuencia_pedidos;
```

Esperado: nombre de base correcto, fichas y recetas existentes, secuencia no nula. Los datos cargados son **ficticios de demostración**.

## 5. Configurar el backend y la clave local

En una terminal PowerShell, desde el proyecto:

```powershell
Set-Location -LiteralPath 'C:\Capstone\MICA_Banqueteria_Proyecto'
Copy-Item .env.example .env
py -c "import secrets; print(secrets.token_urlsafe(50))"
```

Abre `.env` desde VS Code y pega la cadena generada en `MAYA_SECRET_KEY`. Sustituye `MAYA_DB_PASSWORD=CAMBIAR` por la contraseña de tu PostgreSQL. Verifica que `MAYA_DB_NAME=sig_banqueteria_mica`.

No compartas `.env` ni lo subas a GitHub; `.gitignore` lo excluye. `MAYA_DEBUG=1` es **solo para desarrollo local**. Cambia posteriormente las claves/credenciales que figuraban en la versión antigua antes de publicar el código.

## 6. Crear el entorno Python e instalar dependencias

En la misma terminal:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
```

No necesitas activar `Activate.ps1` para ejecutar los pasos; invocar directamente `.venv\Scripts\python.exe` evita problemas con la política de PowerShell. Para activar opcionalmente:

```powershell
.\.venv\Scripts\Activate.ps1
```

Si PowerShell lo bloquea, **no cambies la política global**: utiliza la ruta del ejecutable como en los ejemplos.

## 7. Comprobar Django, migrar y crear administrador

Primero:

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe scripts\diagnosticar.py
```

El diagnóstico debe mostrar conexión a `sig_banqueteria_mica`, las tablas de negocio `OK` y una secuencia de pedidos válida. Es normal que todavía falten las dos tablas `mica_*` antes de migrar.

Después:

```powershell
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe scripts\diagnosticar.py
.\.venv\Scripts\python.exe manage.py createsuperuser
```

Escribe un nombre de usuario y contraseña para tu propia cuenta administrativa. **El usuario de demostración de la tabla `usuario` no es una cuenta válida de autenticación Django.** La migración crea las tablas de MICA y de autenticación; no recrea las 31 tablas de negocio administradas por SQL.

Si `migrate` falla, no ejecutes `makemigrations` al azar ni borres tablas: conserva la salida exacta para investigar.

## 8. Encender el backend

En terminal 1:

```powershell
Set-Location -LiteralPath 'C:\Capstone\MICA_Banqueteria_Proyecto'
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

Deja esta terminal abierta. Django debe mostrar `Starting development server at http://127.0.0.1:8000/`. Comprueba `http://127.0.0.1:8000/admin/` e inicia sesión con tu superusuario.

El servidor Django de desarrollo **no es un despliegue de producción**.

## 9. Instalar y encender React + Vite

Abre **otra terminal** en VS Code:

```powershell
Set-Location -LiteralPath 'C:\Capstone\MICA_Banqueteria_Proyecto\frontend'
npm.cmd ci
npm.cmd run build
npm.cmd run dev -- --host 127.0.0.1 --port 5173
```

Si `npm ci` indica módulos incompatibles, revisa versión de Node y borra/recrea **solo la carpeta `frontend\node_modules`** con npm, nunca la base ni el código. `npm ci` instala según `package-lock.json`.

Abre `http://127.0.0.1:5173` en el navegador. Entra con el administrador Django. El proxy de Vite enviará las solicitudes `/api` al backend local.

## 10. Probar MICA de principio a fin

1. Entra a **Cotizador**. Debe aparecer `MICA · Cotizador inteligente`.
2. Selecciona un cliente de prueba. Puedes seleccionar un evento existente, o indicar fecha y ubicación para uno nuevo.
3. Define comensales, presupuesto, costos de personal/transporte/otros y margen `≥ MICA_MARGEN_MINIMO`.
4. Pulsa **Simular sin guardar**. Deben aparecer alternativas calculadas desde las fichas válidas; con el SQL de demostración puede que solo haya dos, no necesariamente tres.
5. Pulsa **Guardar cotización**. Debe registrarse un identificador MICA y el detalle completo de cada propuesta.
6. Para aceptar: elige una propuesta **dentro de presupuesto**. Si figura stock faltante, confirma el compromiso de compra. Pulsa **Aceptar y generar pedido**.
7. Verifica que aparezca un número `PED-******`, y comprueba el pedido en el listado de Pedidos.
8. Repite el intento de aceptación de la misma cotización: debe responder `409` y **no crear otro pedido**.
9. Prueba presupuesto demasiado bajo: las propuestas deben explicar cuánto exceden el máximo y no permitir aceptación.
10. Escribe una restricción alimentaria. Por seguridad, el sistema debe bloquear la cotización automática hasta contar con alérgenos estructurados y revisión humana.
11. Pulsa **Explicar propuestas** en una cotización guardada: sin API de IA debe responder en modo **reglas**, sin fallar.
12. Verifica que usuarios no administrativos no puedan entrar a endpoints MICA.

**Limitación actual:** cada alternativa corresponde a una preparación, no a un menú completo multi-plato. El inventario consultado no se reserva. Los impuestos/IVA y alérgenos deben definirse antes de uso comercial real.

## 11. Probar la consulta preparada para QR

Después de iniciar sesión, un ejemplo de código cargado en los datos de prueba es `INS-ARROZ-001`. Desde la misma sesión, la futura app podrá consultar:

`GET /api/mica/qr/insumos/INS-ARROZ-001/`

Debe devolver identificador, nombre y stock por bodega. **No es aún un lector de cámara**, ni incorpora el inicio de sesión móvil. Para registrar una entrada/salida existe el endpoint v1 `POST /api/movimientos-inventario/registrar/`; antes de exponerlo a Android deberán reforzarse autorización, identidad del usuario, CSRF/token de sesión y validación de negocio.

## 12. IA gratuita opcional

La parte económica funciona sin proveedor externo. Si decides utilizar el nivel gratuito de Groq **solo para la demostración**, crea una cuenta propia y habilita las credenciales siguiendo sus condiciones vigentes. Añade `GROQ_API_KEY` y el identificador del modelo autorizado en `GROQ_MODEL` **solo en `.env`**. No se envían datos identificatorios del cliente: solo las alternativas y sus precios.

Las cuotas de proveedores gratuitos pueden cambiar o desaparecer; un plan gratuito no garantiza uso indefinido. Si no hay clave o falla la llamada, MICA responde de forma determinista. **No se incluyen claves ni servicios de IA activos en el ZIP**.

## 13. Ejecutar pruebas automáticas (separadas de la base del negocio)

```powershell
Set-Location -LiteralPath 'C:\Capstone\MICA_Banqueteria_Proyecto'
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py test mica.tests.test_motor
```

Las pruebas del motor no escriben registros de negocio. Para probar la integración total necesitarás PostgreSQL real y hacer las verificaciones del punto 10.

## 14. Apagar correctamente

En las dos terminales presiona `Ctrl+C` para detener Vite y Django. PostgreSQL puede permanecer encendido como servicio Windows. No es necesario detenerlo diariamente; nunca borres las bases al cerrar.

## 15. Diagnóstico de errores frecuentes

| Mensaje | Qué verificar |
|---|---|
| `connection refused` / `OperationalError` | PostgreSQL iniciado, host/puerto correctos y `.env` correcto |
| `password authentication failed` | Contraseña de PostgreSQL en `.env` |
| `relation does not exist` | Conectaste otra base o falta inicializar esquema/migrar |
| `pedido_numero_seq does not exist` | Ejecutar únicamente `database/02_SECUENCIA_EN_BD_EXISTENTE.sql` en la base MICA correcta si faltara |
| `No module named django` | Ejecutaste Python global: usa `.venv\Scripts\python.exe` e instala requirements |
| `vite: command not found` | Dentro de `frontend`, ejecuta `npm.cmd ci` |
| `403 CSRF Failed` | Inicia sesión a través de React, recarga y comprueba mismo host + puerto y cookies |
| `No existen alternativas válidas` | Revisa fichas activas, receta, unidades convertibles y costo positivo del insumo |
| `No aparece una tercera propuesta` | Se generan solo las opciones respaldadas por fichas válidas disponibles |

## 16. Qué falta para entregar una versión íntegramente comprobada

- Ejecutar instalación limpia y pruebas con PostgreSQL en tu Windows; adjuntar resultados y capturas.
- Ejecutar `npm.cmd run build` y validar navegación de cada módulo en un navegador real.
- Revisar el modelo de permisos por rol, los módulos antiguos de ventas/dashboard/operación y pruebas de integración; la v1 contiene funciones parciales.
- Diseñar y probar menú multi-preparación, alérgenos, impuestos, cadena de frío y aprobación comercial.
- Incorporar aplicación móvil, autenticación móvil apropiada, lector QR y sus pruebas de seguridad. **No están incluidos aún**.
- Actualizar el documento del alcance original, que excluía IA, antes de presentarla como compromiso formal aprobado.

**No uses esta copia con datos de clientes reales hasta superar las pruebas anteriores y realizar una revisión de seguridad.**
