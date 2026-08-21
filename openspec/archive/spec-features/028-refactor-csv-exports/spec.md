# Feature 028 — Refactor CSV Exports

## Qué hace

- Unifica el estilo del botón "Exportar CSV" en `list.html` al mismo formato `btn-icon btn-outline-success btn-sm` usado en pronósticos (solo ícono + tooltip).
- Elimina 4 exportaciones CSV que solo exportaban metadatos de listado (el valor real está en PDF): WeatherReport, EarlyWarning, TropicalCyclone, StormWarning.
- Agrega 3 nuevas exportaciones CSV con valor real: Contract, Certificate, EmailRecipientList.

## Criterios de aceptación

1. Botón CSV en `list.html` usa `btn-icon btn-outline-success btn-sm` con tooltip, sin texto.
2. Ya no existen las vistas/URLs de export CSV de WeatherReport, EarlyWarning, TropicalCyclone, StormWarning.
3. Existen nuevas vistas/URLs de export CSV para Contract, Certificate, EmailRecipientList.
4. Contract, Certificate y EmailRecipientList ListViews pasan `url_export` en contexto.
5. `python manage.py check` sin errores, todos los tests pasan.
