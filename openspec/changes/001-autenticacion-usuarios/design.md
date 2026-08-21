# 001 · Autenticación y usuarios — Plan

## Enfoque

Login propio con dos backends (LDAP opcional + ModelBackend), gestión de usuarios/grupos con permisos custom, perfiles auto-creados por señal, y middleware de verificación de integridad.

## Implementación

1. **Modelos**: `Profile` (OneToOne→User, avatar, is_ldap) y `GroupProfile` (OneToOne→Group). Señales `post_save` para creación automática.
2. **Backend LDAP**: `LDAP3Backend` en `accounts/ldap3_backend.py`; autentica contra AD, sincroniza grupos staff/superuser.
3. **Login**: `LoginFormView` en `login/views.py`; redirección según rol; log de login/logout con `log_action`.
4. **Usuarios CRUD**: 4 vistas en `accounts/views/user/`; `CustomerRegisterView` para registro público.
5. **Grupos CRUD**: 4 vistas en `accounts/views/group/`; formulario con tabla de permisos del dashboard.
6. **Perfil**: Detail + Update en `accounts/views/profile/`; avatar con PIL (300×300, cuadrado).
7. **Contraseñas**: Change, AdminChange, Reset en `accounts/views/password/`.
8. **Middleware**: `CheckUserProfileMiddleware` en cada request de usuario autenticado.

## Decisiones

- **Señal post_save en vez de CreateView.save()** — garantiza que siempre exista Profile incluso si se crea User por admin, shell o LDAP.
- **LDAP con ldap3** — liviano, sin dependencias del sistema (a diferencia de python-ldap). Sincronización básica (no full AD sync).
- **Permisos custom desde el inicio** — `default_permissions = ()` + 4 custom evita exponer permisos innecesarios y da control granular.

## Riesgos

- **LDAP caído** — el fallback a ModelBackend permite que los usuarios locales sigan entrando; los LDAP quedan bloqueados hasta que el servidor responda.
- **Avatar grandes** — se redimensionan a 300×300 con recorte cuadrado para evitar DoS por imagen y uniformidad visual.
