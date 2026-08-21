# 015 · PDF templates para reportes — Plan

## Enfoque

Usar `publicaciones/pdf_template.html` (102 líneas, existente) como referencia. Cada template recibe el objeto del contexto (`weather_today`, `weather_tomorrow`, `weather_commentary`, `weather_note`) y `logo_base64`.

## Implementación

1. Leer `publicaciones/pdf_template.html` como referencia de estructura
2. Crear 4 templates con: logo base64 + título + resumen + fecha + autor
3. Verificar que las vistas encuentran las templates
4. Tests: llamar cada URL de PDF y verificar response 200 + Content-Type: application/pdf
