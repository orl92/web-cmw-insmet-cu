# 025 · Tareas asíncronas

**Estado:** planificado

## Qué hace

Agrega task queue para operaciones bloqueantes: envío de correos y generación de PDF. Actualmente todo se ejecuta síncronamente en el request thread.

## Criterios de aceptación

- [x] Huey configurado con SqliteHuey (SQLite como broker)
- [x] `send_email_task` — envía correos asíncronamente
- [x] `generate_invoice_pdf_and_email_task` — genera PDF + envía email asíncronamente
- [x] `mail_send` refactorizado: validación y mensajes UI sincrónicos, envío SMTP delegado a `send_email_task`
- [x] PDF generation en facturación extraída a `generate_invoice_pdf_standalone()` y ejecutada como tarea
- [x] `python manage.py check` — sin errores
- [x] `python manage.py test` — 136 tests pasan
