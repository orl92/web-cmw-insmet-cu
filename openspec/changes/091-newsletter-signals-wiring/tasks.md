# Tasks — 091-newsletter-signals-wiring

## Registrar señales

- [ ] `apps/user_auth/apps.py` — Sobreescribir `ready()`: `from . import signals  # noqa: F401`.
- [ ] Verificar que `apps/user_auth/signals.py` se importa al arrancar (`python -c "import apps.user_auth.apps"` o log).

## Verificar/ajustar señales

- [ ] Leer `apps/user_auth/signals.py` y confirmar nombres/campos contra modelos actuales (`Profile.newsletter`, `User.email`, `EmailRecipientList` "Newsletter").
- [ ] Corregir imports obsoletos del refactor 066 si los hay (accounts→user_auth, dashboard→core).
- [ ] Asegurar guard: post_save User no crea/actualiza EmailRecipient si `Profile.newsletter` es False.

## Unicidad

- [ ] `apps/core/models.py` — Agregar `UniqueConstraint(fields=['email', 'list'])` (o equivalente) a `EmailRecipient`.
- [ ] Verificar que no existan duplicados en datos actuales antes de migrar.
- [ ] `python manage.py makemigrations` + `migrate`.

## Tests

- [ ] Test: crear Profile con `newsletter=True` → se crea EmailRecipient en lista "Newsletter".
- [ ] Test: cambiar `newsletter=False` → se elimina el EmailRecipient.
- [ ] Test: cambiar email de User con newsletter activa → se actualiza el EmailRecipient.
- [ ] Test: crear User sin newsletter → no se crea EmailRecipient.

## Verificación

- [ ] `python manage.py check`
- [ ] `python manage.py test apps.user_auth apps.core`
- [ ] Actualizar roadmap.md (mover 091 a Hecho al completar).
- [ ] Commit.
