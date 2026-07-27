# Tasks · 066 Restructure apps

- [ ] **F1.1**: Crear estructura `apps/core/` con __init__, apps.py, models.py
- [ ] **F1.2**: Migrar FileHandlerMixin, SoftDeleteModel, utils desde common/
- [ ] **F1.3**: Migrar error views, mail_send, templatetags, context_processors
- [ ] **F1.4**: Migrar CompanySettings, SiteConfiguration, EmailRecipientList/Recipient
- [ ] **F1.5**: Migrar middleware (CheckUserProfile, MaintenanceMode)
- [ ] **F1.6**: Crear `apps/user_auth/` con Profile, User/Group CRUD, login/logout, password
- [ ] **F1.7**: Migrar señales (post_save de User → Profile) y LDAP backend
- [ ] **F2.1**: Crear `apps/meteo/` con Forecasts, ForecastRegions, ForecastExtendedDay
- [ ] **F2.2**: Migrar WeatherReport, Warning (base), ExcelJSONView, CSV exports
- [ ] **F3.1**: Crear `apps/commercial/` con Customer, Service, ServiceSubscription
- [ ] **F3.2**: Migrar Invoice, InvoiceItem, Contract, Certificate + forms + views + tasks
- [ ] **F3.3**: Mover PROVEEDOR_FACTURA a CompanySettings.proveedor_factura
- [ ] **F4.1**: Reset DB, migraciones, managed=False
- [ ] **F4.2**: makemigrations + migrate + createsuperuser
- [ ] **F5.1**: Actualizar INSTALLED_APPS, URL routing, imports
- [ ] **F5.2**: Eliminar apps legacy del disco
- [ ] **F5.3**: `python manage.py test` pasa
