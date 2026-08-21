# Spec — 031-seguridad-xss-dashboard

## Criterios de aceptación
- `serialize_sub()` escapa `company_name` y `title` con `html.escape()` en Python
- `buildSubsTable()` escapa HTML como defensa en profundidad en JS
- `|safe` se mantiene en las 4 listas de suscripciones (necesario para JSON)
- `except:` en `my_filters.py:504` cambiado a `except (AttributeError, TypeError):`
- `python manage.py test dashboard` pasa sin errores
