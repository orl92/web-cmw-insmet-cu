# Tasks — Feature 029

- [ ] 1. Crear spec/plan/tasks.
- [ ] 2. Agregar `newsletter` a Profile en `accounts/models.py`.
- [ ] 3. Agregar señal `sync_newsletter_recipient` en `accounts/signals.py` (post_save Profile: si newsletter=True y email no vacío → get_or_create "Newsletter" list + EmailRecipient; si newsletter=False → delete EmailRecipient).
- [ ] 4. Agregar señal `update_newsletter_email` en `accounts/signals.py` (post_save User: si cambia email y Profile.newsletter=True → actualizar EmailRecipient en lista Newsletter).
- [ ] 5. Eliminar campo `newsletter` de Customer en `dashboard/models.py`.
- [ ] 6. Crear data migration para copiar newsletter de Customer → Profile.
- [ ] 7. Agregar campo newsletter a `UserUpdateForm` o al template mediante Profile.
- [ ] 8. Modificar `UserUpdateView` para guardar Profile.newsletter.
- [ ] 9. Agregar checkbox newsletter en `user_update.html`.
- [ ] 10. Mover `newsletter` de CustomerSignUpForm a Profile.
- [ ] 11. Ejecutar `makemigrations` y `migrate`.
- [ ] 12. Verificar: `python manage.py check && python manage.py test`.
- [ ] 13. Actualizar roadmap.md.
- [ ] 14. Commit.
