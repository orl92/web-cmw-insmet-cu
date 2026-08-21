# Plan — 037-serializacion-consistente-charts

## Enfoque técnico
1. En `dashboard/views/dashboard/dashboard.py`: envolver las 8 series de temperatura y las 2 de ingresos con `json.dumps()`
2. No requiere cambios en templates ni JS (ya usan `JSON.parse()`)
3. `python manage.py test dashboard`

## App(s) modificada(s)
- dashboard/views/dashboard/dashboard.py
