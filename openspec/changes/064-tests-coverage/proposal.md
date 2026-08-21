# 064 — tests-coverage

## Motivación

La cobertura de tests es desigual entre apps:

- `publications/` usa `tests.py` (archivo suelto) en vez del directorio
  `tests/` y además está vacío (solo imports).
- `home/` solo tiene `test_views.py` — faltan tests de modelos y formularios.
- `dashboard/` tiene tests de modelos, vistas y formularios, pero con
  lagunas en funcionalidades nuevas.
- No hay métrica de cobertura instalada ni reporte.

Estandarizar la estructura y llenar los vacíos garantiza que los
refactors posteriores no introduzcan regresiones.

## Alcance

- `apps/publications/tests.py` → migrar a `tests/` y escribir tests
- `apps/home/tests/test_views.py` — agregar `test_models.py`, `test_forms.py`
- `apps/dashboard/tests/` — auditar qué modelos/views no tienen test
- `config/settings.py` o `tox.ini` — opcional: agregar coverage

## Criterios de Aceptación

1. `apps/publications/tests/` existe como directorio con `__init__.py` y al
   menos un test real.
2. `apps/home/tests/test_models.py` y `test_forms.py` existen con tests.
3. Cada modelo no trivial en `dashboard` tiene test de creación, actualización,
   y (si aplica) soft delete.
4. Cada vista ListView/CreateView/UpdateView tiene al menos un test de
   respuesta HTTP 200/302.
5. `python manage.py test` pasa.
