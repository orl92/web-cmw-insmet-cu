# 091-newsletter-signals-wiring · Newsletter signals wiring

## Motivación

La feature 029 planificó sincronizar el campo `newsletter` del `Profile` con la lista de correo vía señales (`sync_newsletter_recipient`, `update_newsletter_email`) en `apps/user_auth/signals.py`. La auditoría encontró:

1. **Las señales nunca se registran** — `apps/user_auth/signals.py` existe (define las señales) pero **no se importa en ningún lado**. El patrón canónico de Django (`AppConfig.ready()` con `import signals`) no está en `apps/user_auth/apps.py`. Resultado: el checkbox `newsletter` del perfil no tiene efecto; los `EmailRecipient` nunca se crean ni se sincronizan. Es dead feature desde el refactor 066.
2. **Sin registro de ready()** — `apps/user_auth/apps.py` no sobreescribe `ready()`.
3. **Dependencia funcional**: `apps/core/models.py` define `EmailRecipientList`/`EmailRecipient` y `mail_send` usa las listas; la sincronización de newsletter depende de que las señales corran.

## Solución

1. **Registrar las señales**: sobreescribir `ready()` en `apps/user_auth/apps.py` con `from . import signals` (o `import apps.user_auth.signals`).
2. **Verificar que las señales son correctas** contra el modelo actual:
   - `Profile` en `apps/user_auth/models.py` (¿tiene `newsletter`? ¿señal `post_save` de creación de Profile existe?).
   - `User` post_save → `update_newsletter_email`.
   - `EmailRecipientList`/`EmailRecipient` en `apps/core/models.py`.
3. **Unicidad**: `EmailRecipient.email` — la señal usa `get_or_create`; si no hay constraint unique, agregarla (`UniqueConstraint(fields=['email', 'list'])` o `email` único por lista) para que `get_or_create` sea seguro bajo concurrencia.
4. **Tests**:
   - crear Profile con `newsletter=True` → crea EmailRecipient en la lista "Newsletter";
   - desmarcar → elimina el EmailRecipient;
   - cambiar email del User con newsletter activa → actualiza el EmailRecipient.

## Criterios de aceptación

- [ ] `apps/user_auth/apps.py` sobreescribe `ready()` e importa las señales.
- [ ] Toggle `newsletter=True` en Profile crea el `EmailRecipient` correspondiente.
- [ ] Toggle `newsletter=False` elimina el `EmailRecipient`.
- [ ] Cambio de email de User actualiza el `EmailRecipient` (si la newsletter está activa).
- [ ] Unicidad garantizada (constraint) para que `get_or_create` sea seguro.
- [ ] `python manage.py check` y `python manage.py test apps.user_auth apps.core` pasan.
