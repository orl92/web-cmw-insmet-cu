# Plan — Feature 050

## Enfoque técnico

- No se instalan librerías externas (bleach). Se usa un template tag personalizado en `common` o la app `home` que filtra con `strip_tags` y permite solo tags HTML aprobados usando `allow_tags` de `django.utils.html.format_html`.
- Alternativa: usar `{{ value|striptags|linebreaks }}` + un filtro que reintroduzca HTML permitido de forma segura.

## Archivos

| Archivo | Cambio |
|---------|--------|
| `home/templatetags/` | Nuevo filtro `sanitize_html` o similar |
| `templates/pages/home/tiempo/hoy/tiempo_h.html:30` | `{{ ...|safe }}` → `{{ ...|sanitize_html }}` |
| `templates/pages/home/tiempo/mañana/tiempo_m.html:29` | ídem |
| `templates/pages/home/comentarios/tiempo/comentario_tiempo.html:29` | ídem |
| `templates/pages/home/comentarios/nota_meteorologica/nota_meteorologica.html:29` | ídem |

## Detalle

1. Crear `home/templatetags/safe_filters.py` (o agregar a `my_filters.py` si existe en home) con un filtro `sanitize_html` que:
   - Escapa todo con `html.escape()`
   - Reintroduce tags permitidos (`<b>`, `<strong>`, `<i>`, `<em>`, `<p>`, `<br>`, `<ul>`, `<ol>`, `<li>`, `<a>` con href, `<br>`) usando regex
   - Marca el resultado como `mark_safe()`
2. Reemplazar `|safe` por `|sanitize_html` en los 4 templates.
