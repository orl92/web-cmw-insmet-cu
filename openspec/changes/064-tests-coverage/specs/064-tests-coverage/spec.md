# Spec — 064-tests-coverage

## Criterios de Aceptación

1. `apps/publications/tests/` existe como directorio con `__init__.py` y al
   menos un test real.
2. `apps/home/tests/test_models.py` y `test_forms.py` existen con tests.
3. Cada modelo no trivial en `dashboard` tiene test de creación, actualización,
   y (si aplica) soft delete.
4. Cada vista ListView/CreateView/UpdateView tiene al menos un test de
   respuesta HTTP 200/302.
5. `python manage.py test` pasa.
