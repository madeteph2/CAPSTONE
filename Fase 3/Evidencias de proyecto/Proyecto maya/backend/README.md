# Backend Django Banquetería Maya + MICA

Framework real: Django 6.1.2 + DRF 3.18.3, PostgreSQL, autenticación por sesiones con CSRF. No utiliza Node.js, Express ni JWT en backend.

Configuración mediante `.env` en la raíz. Manual completo en `GUIA_EJECUCION_MICA.md`. La app `gestion` conserva modelos legacy `managed=False`; crear tablas de negocio con `database/01_INSTALACION_SOLO_BD_NUEVA.sql` en **una BD nueva y vacía**, antes de ejecutar `python manage.py migrate`. La app `mica` tiene tablas propias con migraciones.
