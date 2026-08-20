# 091 · Newsletter signals wiring — Plan

## Enfoque

Cambio mínimo: registrar las señales existentes y verificar que sincronizan correctamente. No rediseñar el flujo de newsletter.

## Implementación

1. **Registrar señales** — `apps/user_auth/apps.py`:
   - Sobreescribir `ready()`: `from . import signals  # noqa: F401`.
2. **Verificar señales existentes** — leer `apps/user_auth/signals.py` y confirmar contra el modelo real:
   - Nombres de señales (`sync_newsletter_recipient`, `update_newsletter_email`).
   - Campos usados (`Profile.newsletter`, `User.email`, `EmailRecipientList` "Newsletter").
   - Ajustar si el refactor 066 movió nombres/paquetes (ej. `accounts` → `user_auth`, `dashboard` → `core`).
3. **Unicidad** — `apps/core/models.py`:
   - Agregar `UniqueConstraint(fields=['email', 'list'])` (o único por email+lista) a `EmailRecipient`.
   - `makemigrations` + `migrate`.
4. **Tests** — `apps/user_auth/tests/` o `apps/core/tests/`:
   - post_save Profile newsletter=True → EmailRecipient creado.
   - post_save Profile newsletter=False → EmailRecipient eliminado.
   - post_save User cambio email → EmailRecipient actualizado.

## Riesgos

- Las señales pueden referenciar modelos movidos en el refactor 066 (accounts→user_auth) → verificar nombres de imports.
- La señal `post_save User` puede dispararse en creación de superusers/createsuperuser → asegurar guard de no-newsletter.
- Agregar UniqueConstraint requiere que no existan duplicados en datos actuales → verificar antes de migrar.

## Verificación

- `python manage.py check`
- `python manage.py test apps.user_auth apps.core`
- Manual: togglear newsletter en perfil → ver EmailRecipient en admin.
