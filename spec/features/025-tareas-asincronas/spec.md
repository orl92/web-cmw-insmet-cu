# 025 · Tareas asíncronas

**Estado:** planificado

## Qué hace

Agrega task queue para operaciones bloqueantes: envío de correos y generación de PDF. Actualmente todo se ejecuta síncronamente en el request thread.

## Criterios de aceptación

- [ ] Huey o Celery configurado
- [ ] `send_email_task` — envía correos asíncronamente
- [ ] `generate_pdf_task` — genera PDF asíncronamente
- [ ] `mail_send` reemplazado por task asíncrona
- [ ] PDF generation en facturación usa task asíncrona
- [ ] `python manage.py check` — sin errores
