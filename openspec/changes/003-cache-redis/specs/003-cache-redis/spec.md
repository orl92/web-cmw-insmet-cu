# Spec — 003-cache-redis

## Criterios de Aceptación

1. Redis configurado como backend de caché
2. Dashboard carga KPIs desde caché (invalida cada 5 min)
3. `python manage.py test` pasa
4. Fallback graceful si Redis no está disponible (cambiar a `LocMemCache`)
