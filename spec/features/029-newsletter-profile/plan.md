# Plan — Feature 029

## Enfoque técnico

### Apps afectadas: `accounts`, `dashboard`, `common`

### Cambios

1. **`accounts/models.py`** — agregar `newsletter = BooleanField(default=False)` a Profile.
2. **`accounts/signals.py`** — agregar señal `post_save` para Profile que sincroniza con EmailRecipientList "Newsletter". También `post_save`/`post_delete` de User para manejar cambio/eliminación de email.
3. **`dashboard/models.py`** — eliminar campo `newsletter` de Customer.
4. **`dashboard/forms/clientes/forms.py`** — ya removido en Parte A.
5. **`accounts/forms/user/form.py`** — agregar `newsletter` a UserUpdateForm (como campo de Profile).
6. **`accounts/views/user/views.py`** — UserUpdateView debe guardar también Profile.newsletter (modelo `UserUpdateForm` ya maneja User, pero newsletter está en Profile — usar inline formset o campo adicional).
7. **`templates/pages/accounts/users/user_update.html`** — agregar checkbox newsletter.
8. **Data migration** — copiar `Customer.newsletter` → `Profile.newsletter` para usuarios con Customer.
9. **`accounts/forms/user/form.py`** (CustomerSignUpForm) — mover `newsletter` a Profile.
10. **Tests** — actualizar tests existentes, agregar tests de sincronización.
