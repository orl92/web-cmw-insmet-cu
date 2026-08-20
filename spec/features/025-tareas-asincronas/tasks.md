- [x] Agregar `huey` a requirements.txt e instalar
- [x] Crear `config/huey.py` con instancia SqliteHuey
- [x] Agregar `HUEY_DB_PATH` a `config/settings.py`
- [x] Crear `dashboard/tasks.py`:
  - [x] `send_email_task(subject, html_message, from_email, recipients, attachment_name, attachment_content, attachment_mime)`
  - [x] `generate_invoice_pdf_and_email_task(invoice_uuid, site_url)`
- [x] Refactor `dashboard/data/mail_send.py`: validación y mensajes se mantienen sync; `email.send()` → `send_email_task()`
- [x] Extraer `generate_invoice_pdf_standalone()` de `InvoiceCreateView.generate_pdf()` → `dashboard/views/facturacion/utils.py`
- [x] Refactor `InvoiceCreateView.process_batch_invoice()` y `process_manual_invoice()` para llamar task
- [x] Tests para tareas (integrados: 136 tests pasan)
- [x] `python manage.py check && python manage.py test`
- [x] Actualizar roadmap

## Fase 2 — Registro en ready() (ver 089-operacion-produccion)

- [ ] `apps/core/apps.py` — `ready()` importa `apps.core.tasks` (hoy está vacío; `huey_consumer` ve 0 tareas)
- [ ] Registrar tasks de otras apps si existen (commercial, meteo, user_auth)
- [ ] Verificar: `huey_consumer config.huey.huey` loguea las tareas al arrancar
