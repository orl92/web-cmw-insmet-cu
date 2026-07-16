# 003 · Pronósticos detallados

**Estado:** implementado ✅

## Qué hace

CRUD completo de pronósticos meteorológicos detallados organizados en 3 regiones (Costa Norte, Interior, Costa Sur) × 3 períodos (mañana, tarde, noche). Cada celda contiene temperatura, estado del tiempo, dirección y velocidad del viento, y mar (solo costas). Incluye pronóstico extendido a 5 días con temperatura mínima/máxima y tiempo, más datos astronómicos (fase lunar actual y próxima, salida/puesta del sol, índice UV). Vista en dashboard con filtro por fecha y tablas agrupadas.

## Por qué

El pronóstico detallado es el producto principal del centro meteorológico. Unificar 3 regiones en un solo modelo permite visualización comparativa en una sola página y evita 3 formularios separados.

## Criterios de aceptación

- [x] Modelo `Forecasts` con campos para 3 regiones × 3 períodos (temperatura, tiempo, viento, mar).
- [x] Pronóstico extendido: 5 días con fecha, temp min/max, tiempo.
- [x] Datos astronómicos: fase lunar (actual y próxima), salida/puesta sol, índice UV.
- [x] Listado con filtro por fecha; muestra tablas de las 3 regiones + extendido + astronomía.
- [x] Formulario de creación/edición con campos agrupados por región y sección.
- [x] Validación de fecha única (no duplicados).
- [x] Solo usuarios con permiso `dashboard.*_forecast` pueden operar.

## Fuera de alcance

- Pronóstico horario o por hora del día.
- API de pronósticos (feature 008).
- Visualización pública del pronóstico detallado (se entrega en el index, pero la gestión es del dashboard).
