# 009 · Configuración del sitio — Plan

## Enfoque

Tres modelos independientes: SiteConfiguration (maintenance flag), CompanySettings (singleton pk=1), EmailRecipientList + EmailRecipient (maestro-detalle con inline formset). Middleware para maintenance mode. Vistas CRUD estándar.

## Implementación

1. **SiteConfiguration**: modelo con `maintenance_mode` (BooleanField). `MaintenanceModeMiddleware` bloquea no-superusers excepto login page. `MaintenanceModeToggleView` (solo superuser).
2. **CompanySettings**: singleton forzado en `save()` con `self.pk = 1`. Campos fiscales con RegexValidator. `CompanySettingsUpdateView`. Editable inline desde creación de factura vía AJAX.
3. **EmailRecipientList**: CRUD con `inlineformset_factory(EmailRecipientList, EmailRecipient)`. Update restringido a superuser o `creator == request.user`.

## Decisiones

- **Singleton vs tabla de settings** — CompanySettings como singleton (pk=1) es simple y evita joins. Solo una empresa.
- **Middleware vs decorador** — middleware cubre todas las URLs del dashboard sin modificar cada vista.
- **Soft owner check en listas** — el creador puede editar su lista; solo superuser puede editar cualquier lista.

## Riesgos

- **Middleware en orden incorrecto** — debe ir después de authentication middleware pero antes de las vistas del dashboard.
- **CompanySettings no existe** — `get_or_create(pk=1)` en `get_instance()` garantiza que siempre haya un registro.
