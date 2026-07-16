# 013 · Normalizar modelo Forecasts

**Estado:** implementado

## Qué hace

Normaliza el modelo `Forecasts` (~70 campos planos) en modelos relacionados:
- `ForecastRegions` — una fila por región (norte/interior/sur) y período (mañana/tarde/noche)
- `ForecastExtendedDay` — una fila por día extendido (5 días)
- `Forecasts` conserva solo metadatos y datos astronómicos

## Por qué

- 70 campos en un solo modelo viola la primera forma normal (repetición de grupos)
- Dificulta mantenimiento: cualquier cambio requiere tocar 70 field definitions, el form, el template, el JS, etc.
- Impide consultas dinámicas: "dame todas las regiones con temperatura > 30" requiere ORM complejo
- Los templates de crear/actualizar tienen ~1100 líneas cada uno por el rendering manual

## Criterios de aceptación

- [ ] `ForecastRegions` almacena región × período con unique_together
- [ ] `ForecastExtendedDay` almacena día extendido con unique_together
- [ ] Migración de datos: los registros existentes se migran sin pérdida
- [ ] API `/api/forecast/<date>/` devuelve misma estructura JSON (retrocompatible)
- [ ] Página principal (index) funciona igual que antes
- [ ] Dashboard CRUD (crear/editar/listar) funciona igual que antes
- [ ] Dashboard principal (charts) funciona igual que antes
- [ ] `python manage.py test` — todos los tests pasan
- [ ] `python manage.py check` — sin errores

## Fuera de alcance

- Refactor del formulario de creación masiva (Excel import) a los nuevos modelos
- Refactor del JavaScript de subida de Excel (forecast.js)
- Cambios en permisos o URLs
- Eliminación de los campos viejos (se mantienen como respaldo hasta próxima iteración)
