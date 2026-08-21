# Feature 029 — Newsletter en Profile con sincronización automática

## Qué hace

- Mueve el campo `newsletter` del modelo `Customer` al modelo `Profile`.
- Agrega señal `post_save` en Profile que sincroniza automáticamente con `EmailRecipientList` (lista "Newsletter").
- Agrega el checkbox `newsletter` en el template de actualizar usuario (`user_update.html`) para que cualquier usuario (cliente o no) pueda suscribirse.
- Migra los valores `newsletter` existentes de Customer a Profile mediante data migration.

## Criterios de aceptación

1. Profile tiene campo `newsletter` (BooleanField, default=False).
2. Customer ya no tiene campo `newsletter`.
3. Cuando Profile.newsletter cambia a True → se agrega `user.email` a la lista `EmailRecipientList` llamada "Newsletter".
4. Cuando Profile.newsletter cambia a False → se elimina `user.email` de esa lista.
5. Si user.email está vacío, no se agrega.
6. Si user.email cambia, se actualiza en la lista.
7. Al eliminar Profile (User), los emails se limpian de la lista.
8. El checkbox aparece en user_update.html.
9. Data migration copia newsletter de Customer a Profile para clientes existentes.
10. `python manage.py check` sin errores, todos los tests pasan.
