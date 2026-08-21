# 001 · Autenticación y usuarios — Tareas

- [x] Crear modelos Profile y GroupProfile con UUIDField y permisos custom.
- [x] Crear señales post_save para auto-creación de perfiles.
- [x] Implementar LDAP3Backend en accounts/ldap3_backend.py.
- [x] Crear LoginFormView y LogoutRedirectView en login/views.py.
- [x] Implementar UserListView, UserCreateView, UserUpdateView, UserDeleteView.
- [x] Implementar CustomerRegisterView para registro público de clientes.
- [x] Implementar GroupListView, GroupCreateView, GroupUpdateView, GroupDeleteView.
- [x] Implementar ProfileDetailView y ProfileUpdateView con avatar.
- [x] Implementar PasswordChangeView, AdminPasswordChangeView, UserPasswordResetView.
- [x] Implementar CheckUserProfileMiddleware.
- [x] Configurar URLs en accounts/urls.py y login/urls.py.
- [x] Validar con `python manage.py check` y `python manage.py test`.
