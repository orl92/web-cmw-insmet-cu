# Spec — 028-refactor-csv-exports

## Criterios de aceptación

1. Botón CSV en `list.html` usa `btn-icon btn-outline-success btn-sm` con tooltip, sin texto.
2. Ya no existen las vistas/URLs de export CSV de WeatherReport, EarlyWarning, TropicalCyclone, StormWarning.
3. Existen nuevas vistas/URLs de export CSV para Contract, Certificate, EmailRecipientList.
4. Contract, Certificate y EmailRecipientList ListViews pasan `url_export` en contexto.
5. `python manage.py check` sin errores, todos los tests pasan.
