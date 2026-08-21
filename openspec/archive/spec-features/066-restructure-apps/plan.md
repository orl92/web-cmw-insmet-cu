# Plan · 066 Restructure apps

## Fases

### Fase 1: Crear apps core y user_auth
- `apps/core/__init__.py`, `apps.py`, `models.py`, `admin.py`, `urls.py`, `views/`, `forms/`, `templatetags/`, `context_processors.py`, `middleware.py`
- Mover desde `common/`: FileHandlerMixin, SoftDeleteModel, utils, error views, mail_send
- Mover desde `accounts/` + `login/`: Profile, Group, User views/forms, LoginView, LogoutView, Password views
- Mover CompanySettings, SiteConfiguration, EmailRecipientList, EmailRecipient desde `dashboard/models/`
- Registrar señales y huey tasks en `AppConfig.ready()`

### Fase 2: Crear app meteo
- `apps/meteo/__init__.py`, `apps.py`, `models.py`, `admin.py`, `urls.py`, `views/`, `forms/`
- Mover Forecasts, ForecastRegions, ForecastExtendedDay
- Mover WeatherReport
- Warning (solo estructura base, unificación en feature 067)
- ExcelJSONView, CSV exports

### Fase 3: Crear app commercial
- `apps/commercial/__init__.py`, `apps.py`, `models.py`, `admin.py`, `urls.py`, `views/`, `forms/`, `tasks.py`
- Mover Customer, Service, ServiceSubscription, Invoice, InvoiceItem, Contract, Certificate
- Mover forms, views CRUD, tasks Huey
- Migrar PROVEEDOR_FACTURA a CompanySettings

### Fase 4: Reset
- Eliminar DB (`db.sqlite3`)
- Eliminar migraciones en todas las apps
- `managed=False` → `managed=True` (o removido) en modelos legacy
- `python manage.py makemigrations`
- `python manage.py migrate`
- Crear superuser
- `python manage.py test`

### Fase 5: Fixes post-reset
- Corregir imports en todas las apps
- Actualizar INSTALLED_APPS en settings.py
- Actualizar URL routing raíz
- Eliminar apps legacy del settings y del disco
