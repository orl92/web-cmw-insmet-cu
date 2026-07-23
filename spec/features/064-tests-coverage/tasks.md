# Tasks — 064-tests-coverage

## publications — migrar y escribir tests

- [ ] Eliminar `apps/publications/tests.py`
- [ ] Crear `apps/publications/tests/__init__.py`
- [ ] `apps/publications/tests/test_models.py` — test de creación de Author y
      ScientificPublication, verificar `__str__`, FileHandlerMixin cleanup
- [ ] `apps/publications/tests/test_views.py` — test de list, create, update,
      delete (HTTP 200/302, template usado, permisos)
- [ ] Verificar que `python manage.py test publications` ejecuta los tests

## home — agregar test de modelos y formularios

- [ ] `apps/home/tests/test_models.py` — test de context de IndexView,
      WeatherReport display, etc.
- [ ] `apps/home/tests/test_forms.py` — test de validación de formularios
      (si existen en `apps/home/forms.py`)

## dashboard — auditar y llenar gaps

- [ ] Identificar modelos sin test en `apps/dashboard/tests/test_models.py`
      (ej: SiteConfiguration, CompanySettings, EmailRecipientList,
      EmailRecipient, InvoiceItem, ForecastExtendedDay, ForecastRegions)
- [ ] Escribir tests para modelos faltantes: creación, `__str__`, soft delete
- [ ] Identificar vistas sin test en `apps/dashboard/tests/test_views.py`
      (ej: CertificateListView, InvoiceListView, CompanySettingsUpdateView,
      export views)
- [ ] Escribir tests básicos para vistas faltantes (status code, login
      required, template)
- [ ] Identificar formularios sin test en `apps/dashboard/tests/test_forms.py`

## Verificación

- [ ] `python manage.py test` — todo pasa
- [ ] Opcional: instalar `coverage` y generar reporte
