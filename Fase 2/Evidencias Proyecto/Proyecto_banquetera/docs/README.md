# Documentación

# Banquetería Maya — Registro de cambios y avances

**Proyecto:** CAPSTONE 2026 — Ingeniería en Informática  
**Registro de avances:** hasta el 13 de octubre de 2026  
**Repositorio de trabajo:** [madeteph2/CAPSTONE](https://github.com/madeteph2/CAPSTONE)  
**Rama publicada:** `desarrollo-madelaine-v2`  
**Ubicación de la versión publicada:** `Fase 2/Evidencias Proyecto/Proyecto_banquetera/desarrollo-madelaine/`

> **Alcance:** este registro sintetiza las intervenciones y pruebas realizadas después de recibir la base del proyecto. No constituye un diff exhaustivo entre la entrega original y los archivos locales actuales: para identificar líneas, archivos y autorías definitivas debe compararse la versión original con la versión final efectivamente subida.

## 1. Objetivo del sistema

Banquetería Maya es una aplicación de gestión para procesos comerciales y operativos de una empresa de banquetería. El proyecto contempla administración de clientes, pedidos y eventos; y proyecta funcionalidades para fichas técnicas, inventario, ventas, incidencias y cotizaciones.

### Arquitectura empleada en los flujos probados

- **Frontend:** React + Vite, formularios, navegación, vistas y consumo de API JSON.
- **Backend:** Django + Django REST Framework, endpoints, validaciones y lógica de negocio.
- **Persistencia:** PostgreSQL mediante Django ORM / controlador de PostgreSQL.
- **Comunicación:** solicitudes HTTP entre frontend y backend.

**Nota histórica:** en documentación o prototipos previos se consideró Node.js/Express. La arquitectura probada en el trabajo reciente utiliza Django/DRF; actualizar diagramas o documentos que todavía describan la alternativa antigua.

## 2. Base recibida y organización del trabajo

- Se tomó como referencia el código/prototipo inicial y la estructura de archivos compartida por el equipo.
- Se revisó la organización del proyecto y la separación entre frontend, backend, base de datos y documentación.
- Se publicaron los archivos en la rama `desarrollo-madelaine-v2` sin fusionarlos con `main`; la versión está aislada dentro de `desarrollo-madelaine/`.
- Se revisó el script de PostgreSQL y su coherencia con el modelo entidad-relación presentado.

## 3. Correcciones en el frontend

### 3.1 Reparación sintáctica de `App.jsx`

- Revisión de etiquetas y cierres JSX en componentes y fragmentos `<>...</>`.
- Corrección de un operador ternario duplicado en la sección de Eventos.
- Limpieza de caracteres o marcadores Markdown incrustados por error en el código JSX.
- Corrección de expresiones mal formateadas, incluidos controladores `onChange` y `onClick`.
- Revisión de expresiones de renderizado condicional y mapeo de datos.
- Conservación de la navegación, autenticación y secciones existentes al efectuar los ajustes sintácticos.
- Validación sintáctica del archivo revisado; esto **no equivale** a pruebas funcionales completas de todos los módulos.

### 3.2 Orden y mantenibilidad

- Eliminación reportada de **636 líneas vacías** en una versión de trabajo de `App.jsx`, sin modificaciones intencionales de lógica; falta cotejarla con el archivo publicado.
- Entrega de una variante depurada del archivo para facilitar inspección y mantenimiento.
- Identificación de riesgos de integración que requieren revisión en entorno real: dependencia del componente `./Eventos`, rutas de pedidos y manejo de permisos desde servidor.

> **Importante:** el archivo corregido se generó durante el trabajo asistido; verificar que su contenido esté efectivamente incorporado en `frontend/src/App.jsx` antes de marcarlo como cambio publicado.

## 4. Backend y API REST

### 4.1 Eventos

- Revisión del comportamiento de endpoints de eventos.
- Implementación y prueba de creación de eventos mediante `POST /api/eventos/`.
- Respuesta **HTTP 201** observada en una creación exitosa.
- Comprobación de que el evento creado aparece posteriormente en el listado.
- Comprobación de persistencia del registro en PostgreSQL.
- Consulta de eventos mediante `GET`, incluyendo listado y acceso a los registros disponibles.
- Revisión de validación de datos y tratamiento de errores asociados a serializers.

### 4.2 Validaciones y respuestas

- Revisión del patrón `serializer.is_valid()` para detectar entradas incorrectas.
- Revisión de respuestas HTTP con mensajes y detalle de errores de validación.
- Ejecución de una comprobación del proyecto Django con resultado: `System check identified no issues (0 silenced)`.

**Alcance de la evidencia:** esa comprobación valida controles de Django, pero no prueba por sí sola que todas las funcionalidades estén terminadas o libres de fallos.

### 4.3 Elementos revisados, aún no certificados como resueltos

- Configuración y tratamiento de cookies/tokens CSRF en solicitudes del frontend.
- Confirmación de rutas de creación y detalle de pedidos (`/api/pedidos/nuevo/` y `/api/pedidos/{id}/`, según el código revisado).
- Validación de permisos de escritura en backend, sin depender exclusivamente de indicadores como `can_write` en el frontend.
- Persistencia de observaciones de clientes.

## 5. Funcionalidades verificadas

| Módulo | Evidencia de funcionamiento | Situación |
| --- | --- | --- |
| Autenticación | Acceso administrativo realizado durante las pruebas | Verificado en flujo probado |
| Dashboard | Vista principal accesible tras autenticación | Verificado |
| Clientes | Consulta y creación de clientes | Verificado |
| Pedidos | Listado y filtrado de pedidos | Verificado |
| Eventos | Listado y registro de eventos | Verificado |
| API de eventos | `POST /api/eventos/` devuelve HTTP 201 | Verificado |
| Persistencia | Nuevo evento consultable después de recargar | Verificado |

La verificación anterior no implica cobertura de pruebas automatizadas ni validación exhaustiva de escenarios de error.

## 6. Base de datos PostgreSQL

- Revisión del script SQL y contraste con el diagrama entidad-relación utilizado en documentación.
- Identificación de diferencias entre el esquema y el modelo presentado, para su corrección documental.
- Verificación de inserción y posterior consulta de eventos.
- Consulta SQL de la relación entre eventos y pedidos: los **eventos de prueba ID 3 e ID 4** aparecieron sin pedidos asociados en el momento de la revisión.
- Preparación de consultas de inspección de tablas, campos, tipos de datos y registros mediante pgAdmin 4.

### Hallazgos de consistencia del modelo de datos

1. **Eventos:** el pedido referencia el evento, por lo que debe estar correctamente representado en el DER.
2. **Roles y permisos:** distinguir el rol asignado al usuario de la tabla asociativa rol–permiso.
3. **Checklist e incidencias:** representarlos como entidades relacionadas con el pedido de forma independiente, de acuerdo con el script revisado.
4. **Cotizaciones por pedido:** el script revisado no imponía unicidad sobre `cotizacion.id_pedido`; podía admitir varias cotizaciones para un pedido.
5. **Ventas por pedido:** el script revisado tampoco imponía unicidad sobre `venta.id_pedido`.
6. **Estados del pedido:** documentar la referencia `id_estado_pedido`, el catálogo de estados y su historial, en lugar de simplificarla como un campo de texto.
7. **Fichas técnicas e insumos:** homologar denominaciones y relaciones entre DER y SQL.

**Estado de estos puntos:** diferencias detectadas para corregir en el DER y la documentación; no declarar modificada la estructura real hasta ejecutar y verificar migraciones o scripts correspondientes.

## 7. Propuesta de mejora diferencial: cotizador inteligente

Se definió como **valor agregado proyectado** un cotizador asistido por inteligencia artificial, destinado a entregar alternativas de presupuesto en función de variables comerciales como:

- Fecha del evento.
- Cantidad de asistentes o unidades requeridas.
- Presupuesto disponible y montos objetivo.
- Opciones de servicio según las variables ingresadas.

**Estado:** propuesta funcional y de presentación; **no se afirma que el motor de IA esté desarrollado, integrado o probado**.

## 8. Pendientes de implementación o validación

- Formulario de edición de eventos en React y conexión con `PATCH`.
- Visualización del ID del evento como dato no editable en el formulario de edición.
- Confirmación y pruebas integrales de actualización y eliminación de eventos.
- Fichas técnicas y gestión de insumos.
- Inventario y movimientos de stock.
- Cotizador convencional e incorporación posterior de IA.
- Ventas, seguimiento comercial y cierre del proceso.
- Incidencias y checklist operativos.
- Administración de usuarios, roles y permisos de extremo a extremo.
- Revisión exhaustiva de seguridad, CSRF, autorizaciones y validación de datos.
- Homologación del DER, script SQL y documentación con el esquema real.
- Pruebas automatizadas, integración y regresión.

## 9. Evidencias disponibles o registradas

- Acceso al sistema y navegación por el dashboard.
- Consulta/creación de clientes y listado/filtros de pedidos.
- Creación de eventos con respuesta HTTP 201.
- Consulta posterior del evento creado.
- Validación SQL de registros y relaciones de prueba en PostgreSQL.
- Salida de la comprobación de Django sin incidencias del sistema.
- Material preparado para presentación y video demostrativo del sistema.

> Las imágenes, logs y el video deben adjuntarse o enlazarse cuando existan los archivos finales; no se incluyen capturas ficticias.

### Archivos incluidos en la publicación

La publicación de la rama incluyó componentes identificados en el registro de Git: `api_clientes_segura/`, `api_eventos/`, `backend/`, `database/`, `frontend/`, `gestion/`, `manage.py` y `requirements.txt`. La presencia de estos archivos no demuestra por sí sola que todos los módulos estén completos o probados.

### Trazabilidad en GitHub

- **Rama de trabajo:** `desarrollo-madelaine-v2`.
- **Commit de publicación:** `cbb8d89` (`feat: incorpora avances completos de Banqueteria Maya`), según la confirmación de GitHub.
- **Carpeta publicada:** `desarrollo-madelaine/`.
- Los cambios reportados como pruebas locales no deben interpretarse automáticamente como cobertura completa del código publicado.

## 10. Criterios de estado y trazabilidad

Este documento diferencia tres situaciones:

- **Verificado:** flujo o resultado observado mediante pruebas durante el trabajo reciente.
- **Corregido en archivo de trabajo:** cambio realizado en una versión revisada, pendiente de comprobar su incorporación al repositorio publicado.
- **Pendiente:** funcionalidad, corrección o mejora todavía no confirmada como implementada.

> **Advertencia de integración:** este registro describe la versión situada en `desarrollo-madelaine/`. No se han reemplazado automáticamente los directorios `frontend/`, `backend/` y `database/` que existen en la raíz de `Proyecto_banquetera/`.
