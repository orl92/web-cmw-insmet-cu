# 025 · Tareas asíncronas — Plan

## Enfoque

Usar Huey + SQLite (archivo `huey.db`) como broker. No requiere Redis ni servicios externos.

## Decisión de diseño

- `mail_send()` mantiene la validación y mensajes UI sincrónicamente; solo el envío SMTP se delega a la tarea. Esto preserva los mensajes de éxito/error en la interfaz.
- La generación de PDF de facturación (wkhtmltopdf) se extrae a función standalone y se ejecuta como tarea, junto con el envío del email.

## Archivos a modificar/crear

| Archivo | Acción |
|---|---|
| `requirements.txt` | + `huey` |
| `config/huey.py` | Crear — instancia `SqliteHuey` |
| `config/settings.py` | + `HUEY_DB_PATH` |
| `dashboard/tasks.py` | Crear — `send_email_task`, `generate_invoice_pdf_and_email_task` |
| `dashboard/data/mail_send.py` | Refactor — delegar `email.send()` a task |
| `dashboard/views/facturacion/views.py` | Refactor — llamar task en vez de inline PDF+email |
| `dashboard/views/facturacion/utils.py` | + `generate_invoice_pdf_standalone()` extraída de `InvoiceCreateView` |

## Ejecución del worker

```bash
huey_consumer.py config.huey.huey
```
