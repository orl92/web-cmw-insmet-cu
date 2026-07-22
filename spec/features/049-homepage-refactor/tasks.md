# Tasks — Feature 049

- [ ] `templates/pages/home/index.html` - Cambiar `<spam>` por `<span>` en líneas 212, 216
- [ ] `templates/includes/home/forecast_region_card.html` - Crear partial con bloque de región climática (recibe región, datos morning/afternoon/night)
- [ ] `templates/pages/home/index.html` - Reemplazar 3 bloques repetidos por `{% include %}` con región
- [ ] `templates/pages/home/index.html` - Reemplazar `class="invisible"` por `{% if %}` condicional en Interior
- [ ] `templates/pages/home/index.html` - Eliminar tooltips redundantes (temperatura, viento cuando repiten el texto)
- [ ] `templates/pages/home/index.html` - Refactorizar SVG índice UV: calcular posición del indicador por fórmula
- [ ] `templates/pages/home/index.html` - Agregar `loading="lazy"` a imágenes below the fold
- [ ] `templates/includes/home/empty_state.html` - Crear partial con SVG de "sin datos" parametrizado
- [ ] `templates/pages/home/index.html` - Reemplazar 3 empty states por `{% include %}`
- [ ] `python manage.py check` — verificar sin errores
- [ ] `python manage.py test home` — tests pasan
