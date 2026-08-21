# 002 · Portal público meteorológico — Plan

## Enfoque

Modelos compartidos con `FileHandlerMixin`, vistas públicas de solo lectura (DetailView/ListView), vistas de dashboard con CRUD completo, generación de PDF con xhtml2pdf, y envío de correos con `mail_send()`.

## Implementación

1. **Modelos**: `WeatherToday`, `WeatherTomorrow`, `WeatherCommentary`, `WeatherNote` (con `FileHandlerMixin`), `BaseWarning` (abstracta) → `EarlyWarning`, `TropicalCyclone`, `StormWarning`. Cada uno con permisos custom.
2. **Público**: 7 vistas en `home/views/` — DetailViews para tiempo/comentarios/notas (último registro del día), ListViews para avisos (solo vigentes).
3. **Dashboard CRUD**: 4 vistas por modelo (list, create, update, delete) + detail + PDF. 7 modelos × ~6 vistas = ~42 clases.
4. **PDF**: `WeatherTodayPDFView` y similares renderizan template HTML con xhtml2pdf; logo en Base64; filename con fecha.
5. **Correo**: `dashboard/data/mail_send.py` → `mail_send()` envía HTML con PDF adjunto a los `EmailRecipient` de la lista seleccionada.
6. **Detección de cambios**: En vistas Create/Update se comparan campos relevantes (`summary`, `file`, `email_recipient_list`) antes de enviar correo.

## Decisiones

- **DetailView público con `.first()` por fecha** — siempre muestra el registro más reciente; no hay URL con UUID público.
- **`BaseWarning` abstracta** — evita tabla separada, cada tipo de aviso es su propio modelo con su propio permiso.
- **Correo solo en cambios relevantes** — evita spam al editar campos no visibles al público.

## Riesgos

- **PDF falla si falta wkhtmltopdf** — `xhtml2pdf` no requiere wkhtmltopdf (usa pisa), pero la calidad de renderizado depende del CSS.
- **Archivos huérfanos** — `FileHandlerMixin` los limpia automáticamente al borrar o reemplazar el archivo.
