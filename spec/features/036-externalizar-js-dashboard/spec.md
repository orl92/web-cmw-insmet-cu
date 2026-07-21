# 036 — Externalizar JS del dashboard a static/js/dashboard.js

## Qué hace
Mueve las ~300 líneas de JS inline de ApexCharts desde `dashboard.html` a
`static/dist/js/dashboard.js`, usando atributos `data-*` para pasar datos
dinámicos. Sigue el patrón de convención del proyecto (data-* en HTML).

## Criterios de aceptación
- dashboard.html tiene data-* attributes con los datos de charts
- static/dist/js/dashboard.js contiene toda la lógica ApexCharts
- CSS inline extraído a static/dist/css/dashboard.css
- Dashboard funciona idéntico en modo claro/oscuro
- `python manage.py collectstatic --link --no-input`
- Tests pasan
