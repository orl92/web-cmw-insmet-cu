# Plan — 036-externalizar-js-dashboard

## Enfoque técnico
1. Agregar atributos data-* a los divs de charts en dashboard.html:
   - `#temperatureTrendChart`: data-labels, data-series-north-max, etc.
   - `#incomeChart`: data-billed, data-paid, data-months
   - `#subscriptionsChart`: data-active, data-pending, etc.
2. Mover JS inline a `static/dist/js/dashboard.js`
3. dashboard.js lee datos de data-* attributes al inicializar
4. Mover CSS inline a `static/dist/css/dashboard.css`
5. dashboard.html solo importa los estáticos

## Apps modificadas
- templates/pages/dashboard/dashboard.html

## Archivos nuevos
- static/dist/js/dashboard.js
- static/dist/css/dashboard.css
