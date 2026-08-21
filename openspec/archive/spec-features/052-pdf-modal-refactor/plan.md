# Plan — Feature 052

## Enfoque técnico

- Identificar el bloque de modal PDF en uno de los templates existentes.
- Copiarlo a `templates/includes/home/pdf_modal.html`.
- Reemplazar el bloque en cada template por `{% include %}`.
- No requiere cambios de modelo, vista ni tests.

## Archivos

| Archivo | Cambio |
|---------|--------|
| `templates/includes/home/pdf_modal.html` | Nuevo: contenido del modal PDF extraído |
| `templates/pages/home/avisos/avisos.html` | Reemplazar bloque por `{% include %}` |
| `templates/pages/home/tiempo/hoy/tiempo_h.html` | ídem |
| `templates/pages/home/tiempo/mañana/tiempo_m.html` | ídem |
| `templates/pages/home/comentarios/tiempo/comentario_tiempo.html` | ídem |
| `templates/pages/home/comentarios/nota_meteorologica/nota_meteorologica.html` | ídem |
| `templates/pages/home/servicios/servicios_publicos.html` | ídem |
| `templates/pages/home/servicios/servicios_comerciales.html` | ídem |
