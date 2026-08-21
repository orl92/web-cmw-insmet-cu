# 001 · Autenticación y usuarios

**Estado:** implementado ✅

## Qué hace

Sistema completo de autenticación y gestión de usuarios con dos modos de ingreso: LDAP corporativo (opcional) y Django Auth tradicional. Incluye registro público de clientes, CRUD de usuarios y grupos con permisos granulares, perfiles con avatar, cambio de contraseña (auto y admin), reseteo de contraseña por correo, y middleware que verifica integridad del perfil.

## Por qué

Base del sistema: sin autenticación no hay dashboard, ni clientes, ni personalización. El doble backend (LDAP + Django Auth) cubre tanto al personal del instituto (LDAP) como a clientes externos (registro público).

## Criterios de aceptación

- [x] Login/logout con `LoginFormView` y `LogoutRedirectView`; staff redirige a dashboard, no-staff al portal público.
- [x] Backend LDAP autentica contra Active Directory si `LDAP_SERVER_URI` está configurado; fallback a ModelBackend.
- [x] Registro público de clientes crea User + Customer + asigna grupo "Clientes".
- [x] CRUD de usuarios (list, create, update, delete) con permisos `auth.*_user`.
- [x] CRUD de grupos con tabla de permisos filtrada a modelos del dashboard.
- [x] Perfil de usuario (Profile) se crea automáticamente por señal `post_save`; avatar redimensionado a 300×300 cuadrado.
- [x] Cambio de contraseña propio y por admin; bloqueado para usuarios LDAP.
- [x] Reseteo de contraseña por correo con plantilla HTML personalizada.
- [x] Middleware `CheckUserProfileMiddleware` garantiza Profile existente y datos completos.

## Fuera de alcance

- Autenticación OAuth2 / SSO con otros proveedores.
- Autoregistro de usuarios sin verificación de correo.
