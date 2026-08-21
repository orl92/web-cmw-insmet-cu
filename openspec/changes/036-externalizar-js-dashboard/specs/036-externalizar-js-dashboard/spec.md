# Spec — 036-externalizar-js-dashboard

## Criterios de aceptación
- dashboard.html tiene data-* attributes con los datos de charts
- static/dist/js/dashboard.js contiene toda la lógica ApexCharts
- CSS inline extraído a static/dist/css/dashboard.css
- Dashboard funciona idéntico en modo claro/oscuro
- `python manage.py collectstatic --link --no-input`
- Tests pasan
