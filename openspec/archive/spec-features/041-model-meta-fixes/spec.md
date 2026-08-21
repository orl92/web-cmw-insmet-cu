# 041 — Model Meta fixes (ordering, permisos, singleton)

## Qué hace
Corrige 3 tipos de issues en modelos de `dashboard/models.py`:

1. **Meta.ordering faltante** en 8 modelos: SiteConfiguration, CompanySettings, Province, Town, Station, Forecasts, EmailRecipientList, EmailRecipient
2. **Contract** sin `default_permissions = ()` ni permisos custom (`view_contract`, etc.) — inconsistente con el resto del proyecto
3. **CompanySettings.save()** fuerza `pk=1` pero permite múltiples instancias

## Criterios de aceptación
- Los 8 modelos tienen `Meta.ordering` con campo razonable
- `Contract.Meta` tiene `default_permissions = ()` y los 4 permisos custom
- `CompanySettings` previene creación de segunda instancia (singleton real)
- `python manage.py test` pasa
