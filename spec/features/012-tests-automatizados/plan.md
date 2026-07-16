# 012 · Tests automatizados — Plan

## Enfoque

Reemplazar cada `tests.py` stub por un directorio `tests/` con módulos por tipo de test (modelos, vistas, formularios, API). Usar `django.test.TestCase`, `Client`, `APITestCase` y `unittest.mock`.

## Implementación

1. **common/tests/** — tests sin DB (SimpleTestCase) para `get_img_path`, `get_moon_img_path`, `get_sun_img_path`, `pdf_upload_path`, `image_upload_path`, `FileHandlerMixin`.
2. **accounts/tests/** — `test_models.py` (Profile, GroupProfile), `test_views.py` (CRUD de usuarios/grupos con permisos), `test_forms.py` (formularios de usuario/grupo/perfil).
3. **dashboard/tests/** — `test_models.py` (todos los modelos: creación, validaciones, __str__, FileHandlerMixin, soft delete, singleton), `test_views.py` (CRUD principales con log_action), `test_forms.py`.
4. **api/tests/** — `test_api.py` con APITestCase para stations, observations, forecasts.
5. **home/tests/** — `test_views.py` para páginas públicas (tiempo hoy/mañana, avisos, modelos, satélites).
6. **login/tests/** — `test_views.py` para login/logout.
7. Migrar `tests.py` → `tests/__init__.py` que importa todo.

## Decisiones

- **tests/ en vez de tests.py**: mejor organización, separación por tipo.
- **mock para servicios externos**: `unittest.mock.patch` para `requests.get` en vistas de modelos/satélites.
- **Fixture data via setUp**: crear objetos directamente en `setUpTestData` o `setUp`, no se usan fixtures JSON.
- **No se usa pytest**: mantener consistencia con `python manage.py test` de Django.

## Riesgos

- **settings.py ejecuta código al importarse** — puede fallar si no hay `.env`. Ya existe `.env` en desarrollo, pero en CI habría que generarlo.
- **FileHandlerMixin tests** — requieren simular archivos sin depender del filesystem real. Usar `tempfile` + `SimpleUploadedFile`.
- **Custom permissions** — los modelos no tienen permisos por defecto. Los tests de vistas deben asignar permisos explícitamente o usar usuarios superuser.
