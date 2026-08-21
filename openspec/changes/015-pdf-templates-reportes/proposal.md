# 015 · PDF templates para reportes

**Estado:** implementado

## Qué hace

Crea las 4 templates PDF que faltan en disco para las vistas `*PDFView` de reportes meteorológicos (WeatherToday, WeatherTomorrow, WeatherCommentary, WeatherNote). Actualmente estas vistas referencian `pdf_template.html` que no existe → error 500.

## Criterios de aceptación

- [ ] `pages/dashboard/tiempo/hoy/pdf_template.html` existe y es funcional
- [ ] `pages/dashboard/tiempo/manana/pdf_template.html` existe y es funcional
- [ ] `pages/dashboard/comentarios/tiempo/pdf_template.html` existe y es funcional
- [ ] `pages/dashboard/comentarios/nota_meteorologica/pdf_template.html` existe y es funcional
- [ ] Cada PDF se descarga con nombre y contenido correctos
- [ ] `python manage.py test` — todos pasan
