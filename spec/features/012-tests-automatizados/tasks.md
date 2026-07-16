# 012 · Tests automatizados — Tareas

### common/

- [x] Crear `common/tests/__init__.py`
- [x] Crear `common/tests/test_utils.py` — 13 tests (get_img_path, moon/sun paths, upload paths, log_action, FileHandlerMixin)

### accounts/

- [x] Crear `accounts/tests/__init__.py`
- [x] Crear `accounts/tests/test_models.py` — Profile creation signal, GroupProfile
- [x] Crear `accounts/tests/test_views.py` — User CRUD, Group CRUD, profile views, permissions
- [x] Crear `accounts/tests/test_forms.py` — User form, Group form

### dashboard/

- [x] Crear `dashboard/tests/__init__.py`
- [x] Crear `dashboard/tests/test_models.py` — todos los modelos (22+): creación, validaciones, __str__, FileHandlerMixin, soft delete, singleton
- [x] Crear `dashboard/tests/test_views.py` — vistas CRUD (provincias, estaciones, pronósticos, weather reports)
- [x] Crear `dashboard/tests/test_forms.py` — formularios (Province)

### api/

- [x] Crear `api/tests/__init__.py`
- [x] Crear `api/tests/test_api.py` — 7 tests (StationListAPI, ForecastAPI, schema endpoint)

### home/

- [x] Crear `home/tests/__init__.py`
- [x] Crear `home/tests/test_views.py` — 13 tests (index, servicios, satélites, publicaciones, 4 tipos de weather report)

### login/

- [x] Crear `login/tests/__init__.py`
- [x] Crear `login/tests/test_views.py` — 4 tests (login form, valid/invalid credentials, logout redirect)

### Migración y verificación

- [x] Reemplazar `tests.py` por `tests/` en cada app
- [x] Ejecutar `python manage.py test` — 116 tests, todos pasan
- [x] Actualizar `spec/constitution/roadmap.md` — mover 012 a "Hecho"
