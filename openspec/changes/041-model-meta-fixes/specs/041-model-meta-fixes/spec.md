# Spec — 041-model-meta-fixes

## Criterios de aceptación
- Los 8 modelos tienen `Meta.ordering` con campo razonable
- `Contract.Meta` tiene `default_permissions = ()` y los 4 permisos custom
- `CompanySettings` previene creación de segunda instancia (singleton real)
- `python manage.py test` pasa
