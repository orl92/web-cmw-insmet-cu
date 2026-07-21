# 037 — Serialización consistente de datos para charts

## Qué hace
Serializa todas las series de datos de los charts ApexCharts con `json.dumps()` en `dashboard.py` para consistencia. Actualmente `temperature_labels` e `income_months` usan `json.dumps()` pero las series numéricas (`max_temperatures_north`, `income_billed_data`, etc.) se pasan como listas Python crudas que Django renderiza con `str()`.

Aunque `str([1, 2, 3])` produce `[1, 2, 3]` que es JSON válido para números, si en el futuro se agregara un string con caracteres especiales a alguna serie, el `JSON.parse()` en `dashboard.js` fallaría.

## Criterios de aceptación
- `max_temperatures_north`, `min_temperatures_north`, `max_temperatures_inland`, `min_temperatures_inland`, `max_temperatures_south`, `min_temperatures_south`, `income_billed_data`, `income_paid_data` se serializan con `json.dumps()`
- `dashboard.js` sigue funcionando con `JSON.parse()`
- Tests pasan
