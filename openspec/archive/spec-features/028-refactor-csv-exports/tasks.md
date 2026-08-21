# Tasks — Feature 028

## Tareas

- [ ] 1. Crear spec/plan/tasks (feature 028).
- [ ] 2. Editar `templates/layouts/list.html`: cambiar botón a `btn-icon btn-outline-success btn-sm` con tooltip.
- [ ] 3. Editar `dashboard/views/exports.py`:
  - Eliminar `WeatherReportCSVExportView`, `EarlyWarningCSVExportView`, `TropicalCycloneCSVExportView`, `StormWarningCSVExportView`.
  - Agregar `ContractCSVExportView`, `CertificateCSVExportView`, `EmailRecipientListCSVExportView`.
  - Eliminar imports de modelos eliminados; agregar imports de Contract, Certificate, EmailRecipientList.
- [ ] 4. Editar `dashboard/urls.py`:
  - Eliminar 4 URLs: `exportar_csv_tiempo`, `exportar_csv_alertas`, `exportar_csv_ciclones`, `exportar_csv_tormentas`.
  - Agregar 3 URLs: `exportar_csv_contratos`, `exportar_csv_certificados`, `exportar_csv_listas_correo`.
- [ ] 5. Editar `dashboard/views/tiempo/views.py`: eliminar línea `context['url_export']`.
- [ ] 6. Editar `dashboard/views/avisos/alertas_tempranas/views.py`: eliminar línea `context['url_export']`.
- [ ] 7. Editar `dashboard/views/avisos/ciclones_tropicales/views.py`: eliminar línea `context['url_export']`.
- [ ] 8. Editar `dashboard/views/avisos/tormentas/views.py`: eliminar línea `context['url_export']`.
- [ ] 9. Editar `dashboard/views/contratos/views.py`: agregar `context['url_export']`.
- [ ] 10. Editar `dashboard/views/certificados/views.py`: agregar `context['url_export']`.
- [ ] 11. Editar `dashboard/views/email_recipient/views.py`: agregar `context['url_export']`.
- [ ] 12. Verificar: `python manage.py check && python manage.py test`.
- [ ] 13. Actualizar `spec/constitution/roadmap.md`.
- [ ] 14. Commit.
