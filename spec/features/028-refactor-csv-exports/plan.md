# Plan — Feature 028

## Enfoque técnico

### App afectada: `dashboard/`

### Archivos a modificar

1. **`templates/layouts/list.html`** — cambiar botón export a `btn-icon btn-outline-success btn-sm` con tooltip.
2. **`dashboard/views/exports.py`** — eliminar `WeatherReportCSVExportView`, `EarlyWarningCSVExportView`, `TropicalCycloneCSVExportView`, `StormWarningCSVExportView`; agregar `ContractCSVExportView`, `CertificateCSVExportView`, `EmailRecipientListCSVExportView`.
3. **`dashboard/urls.py`** — eliminar 4 URLs de export eliminados; agregar 3 URLs nuevas.
4. **`dashboard/views/tiempo/views.py`** — eliminar `context['url_export']`.
5. **`dashboard/views/avisos/alertas_tempranas/views.py`** — eliminar `context['url_export']`.
6. **`dashboard/views/avisos/ciclones_tropicales/views.py`** — eliminar `context['url_export']`.
7. **`dashboard/views/avisos/tormentas/views.py`** — eliminar `context['url_export']`.
8. **`dashboard/views/contratos/views.py`** — agregar `context['url_export']`.
9. **`dashboard/views/certificados/views.py`** — agregar `context['url_export']`.
10. **`dashboard/views/email_recipient/views.py`** — agregar `context['url_export']`.
11. **`dashboard/models.py`** — revisar imports, quitar los no usados.
12. **`spec/constitution/roadmap.md`** — mover 028 a Hecho.
