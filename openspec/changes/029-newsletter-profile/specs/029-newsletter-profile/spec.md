# Spec — 029-newsletter-profile

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
