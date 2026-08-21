## Criterios de aceptación

- [ ] `apps/user_auth/apps.py` sobreescribe `ready()` e importa las señales.
- [ ] Toggle `newsletter=True` en Profile crea el `EmailRecipient` correspondiente.
- [ ] Toggle `newsletter=False` elimina el `EmailRecipient`.
- [ ] Cambio de email de User actualiza el `EmailRecipient` (si la newsletter está activa).
- [ ] Unicidad garantizada (constraint) para que `get_or_create` sea seguro.
- [ ] `python manage.py check` y `python manage.py test apps.user_auth apps.core` pasan.
