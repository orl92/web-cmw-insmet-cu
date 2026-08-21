# Spec — 009-configuracion-sitio

## Criterios de aceptación

- [x] Modo mantenimiento toggleable por superuser desde el dashboard.
- [x] Middleware bloquea no-superusers con 503 cuando maintenance_mode=True.
- [x] Página de login excluida del bloqueo.
- [x] CompanySettings como singleton (pk=1), editable desde el dashboard.
- [x] Validación de REEUP, NIT, cuenta bancaria y teléfonos.
- [x] CRUD de listas de correo con destinatarios inline (formset).
- [x] Update de lista restringido a superuser o creador.
