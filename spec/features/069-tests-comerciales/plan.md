# Plan — 069 tests-comerciales

## Enfoque

Usar `django.test.TestCase` (no pytest, no factory_boy), inline ORM helpers, mismo patrón que `apps/user_auth/tests/test_views.py`.

## Estructura de archivos

```
apps/commercial/tests/
├── __init__.py
├── test_models.py
├── test_forms.py
├── test_views.py
└── test_tasks.py
```

## Helpers compartidos (cada archivo define los suyos)

- `_make_user()` — crea User con datos completos
- `disable_maintenance_mode()` — `SiteConfiguration.objects.get_or_create(defaults={'maintenance_mode': False})`
- `_make_customer()` — crea Customer + User completo
- `_make_service()` — crea Service con user
- `_make_subscription()` — crea ServiceSubscription con customer + service
- `FileHandlingTestCase` — para modelos con FileField (Service, Invoice, Certificate)

## Orden de implementación

1. `test_models.py` — foundation, sin dependencias de forms/views
2. `test_forms.py` — depende de modelos
3. `test_views.py` — depende de modelos + forms
4. `test_tasks.py` — depende de modelos + utils

## Patrón por test

```python
class XxxTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        disable_maintenance_mode()
        cls.user = _make_user('testuser')
        ...

    def test_login_required(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, f'/accounts/login/?next={self.url}')
```
