# Spec — 003-pronosticos-detallados

## Criterios de aceptación

- [x] Modelo `Forecasts` con campos para 3 regiones × 3 períodos (temperatura, tiempo, viento, mar).
- [x] Pronóstico extendido: 5 días con fecha, temp min/max, tiempo.
- [x] Datos astronómicos: fase lunar (actual y próxima), salida/puesta sol, índice UV.
- [x] Listado con filtro por fecha; muestra tablas de las 3 regiones + extendido + astronomía.
- [x] Formulario de creación/edición con campos agrupados por región y sección.
- [x] Validación de fecha única (no duplicados).
- [x] Solo usuarios con permiso `dashboard.*_forecast` pueden operar.
