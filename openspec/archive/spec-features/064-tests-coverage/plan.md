# Plan — 064-tests-coverage

## Estrategia

1. **publications**: eliminar `tests.py`, crear `tests/` con
   `test_models.py`, `test_views.py`. Tests básicos: crear ScientificPublication y Author, verificar `__str__`, permisos, PDF upload.

2. **home**: crear `test_models.py` (IndexView context, WeatherReport data) y
   `test_forms.py` (si hay formularios en home/forms.py).

3. **dashboard**: auditar qué modelos no tienen test. Priorizar:
   - Modelos con FileHandlerMixin → test de limpieza de archivos.
   - Modelos con SoftDeleteModel → test de soft/hard delete.
   - Vistas sin test → al menos test de status code y template usado.

## Orden recomendado

1. publications (error más visible: tests.py vacío)
2. home (segundo más urgente: app pública sin tests de modelos)
3. dashboard coverage audit

## Riesgos

- Migrar de `tests.py` a `tests/` puede confundir el test runner si queda
  el `.pyc` o el archivo original. Asegurarse de eliminar `tests.py`.
- Tests de vistas requieren fixtures o datos de setup más elaborados.
