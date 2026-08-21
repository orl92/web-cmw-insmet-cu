# 074 — cache-redis

## Motivación

No hay capa de caché configurada. Endpoints públicos de API, list views con muchos registros y el dashboard se regeneran en cada request. Redis como backend de caché mejora tiempos de respuesta y reduce carga en DB.

## Alcance

- Agregar Redis a `requirements.txt` (o `django-redis`)
- Configurar `CACHES` en `settings.py`
- Cachear template fragments del dashboard (KPIs, charts data)
- Cachear querysets de list views con timeout corto (5 min)

## Criterios de Aceptación

1. Redis configurado como backend de caché
2. Dashboard carga KPIs desde caché (invalida cada 5 min)
3. `python manage.py test` pasa
4. Fallback graceful si Redis no está disponible (cambiar a `LocMemCache`)
