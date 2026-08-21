# Spec — 037-serializacion-consistente-charts

## Criterios de aceptación
- `max_temperatures_north`, `min_temperatures_north`, `max_temperatures_inland`, `min_temperatures_inland`, `max_temperatures_south`, `min_temperatures_south`, `income_billed_data`, `income_paid_data` se serializan con `json.dumps()`
- `dashboard.js` sigue funcionando con `JSON.parse()`
- Tests pasan
