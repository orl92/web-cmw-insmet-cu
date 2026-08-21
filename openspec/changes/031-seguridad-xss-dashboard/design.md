# Plan — 031-seguridad-xss-dashboard

## Enfoque técnico
1. `dashboard/views/dashboard/views.py`: agregar `import html`, escapar con `html.escape()`
   en `serialize_sub()` antes de `json.dumps()`. `|safe` se mantiene en template.
2. `dashboard.html`: agregar función `escapeHtml()` en JS y usarla en `buildSubsTable()`
3. `my_filters.py`: cambiar `except:` a `except (AttributeError, TypeError):`
4. Tests: verificar que datos con `<script>` se renderizan como texto

## App(s) modificada(s)
- dashboard (views, template, templatetags)

## Archivos nuevos
- Ninguno
