# 044 — Template fixes (lang, static path)

## Qué hace
Corrige issues de templates:

1. **`templates/layouts/base.html:11`** — `<html lang="en">` debería ser `lang="es"` (proyecto en español)
2. **`templates/layouts/base.html:26`** — `{% static '' %}dist/js/tabler-theme.min.js` debería ser `{% static 'dist/js/tabler-theme.min.js' %}`

## Criterios de aceptación
- `lang="es"` en base.html
- Static path limpio
- `python manage.py test` pasa
