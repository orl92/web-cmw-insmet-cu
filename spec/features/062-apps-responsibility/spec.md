# 062 — apps-responsibility

## Motivación

La app `dashboard/` concentra ~21 modelos que cubren al menos 5 dominios de
negocio distintos: geografía (Province, Town, Station), meteorología
(Forecasts, BaseWarning, WeatherReport), CRM (Customer, Service,
ServiceSubscription), facturación (Invoice, InvoiceItem, Contract),
configuración (SiteConfiguration, CompanySettings) y correos
(EmailRecipientList, EmailRecipient).

Esto viola el principio de responsabilidad única: la app es difícil de
mantener, los tests son lentos, los acoplamientos entre dominios no son
explícitos, y cualquier cambio requiere entender toda la app.

## Alcance

- `apps/dashboard/models.py` (todo)
- `apps/dashboard/views/` (todo)
- `apps/dashboard/forms/` (todo)
- `apps/dashboard/urls.py`
- `config/urls.py`
- `config/settings.py` (INSTALLED_APPS)

## Criterios de Aceptación

1. Feature spec creada para cada nuevo dominio extraído (geografía,
   facturación, CRM, correos).
2. Cada nueva app tiene su propio `models.py`, `views/`, `forms/`, `urls.py`,
   `tests/`.
3. Las vistas del dashboard referencian las nuevas apps mediante imports.
4. No se rompe ninguna URL existente (redirecciones o compatibilidad).
5. Tests existentes pasan.
