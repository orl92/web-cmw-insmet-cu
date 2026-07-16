# 009 · Configuración del sitio

**Estado:** implementado ✅

## Qué hace

Tres funcionalidades de configuración del sistema: (1) modo mantenimiento que bloquea todo el dashboard a no-superusers mostrando una página 503, (2) configuración de datos fiscales de la empresa (nombre, dirección, REEUP, NIT, cuenta bancaria, etc.) como singleton, y (3) gestión de listas de correo electrónico con destinatarios inline para notificaciones.

## Por qué

El modo mantenimiento permite desplegar cambios sin que los usuarios vean errores. Los datos fiscales son necesarios para facturación. Las listas de correo son el mecanismo de suscripción a notificaciones meteorológicas.

## Criterios de aceptación

- [x] Modo mantenimiento toggleable por superuser desde el dashboard.
- [x] Middleware bloquea no-superusers con 503 cuando maintenance_mode=True.
- [x] Página de login excluida del bloqueo.
- [x] CompanySettings como singleton (pk=1), editable desde el dashboard.
- [x] Validación de REEUP, NIT, cuenta bancaria y teléfonos.
- [x] CRUD de listas de correo con destinatarios inline (formset).
- [x] Update de lista restringido a superuser o creador.

## Fuera de alcance

- Configuración de logo o branding desde el dashboard.
- Múltiples empresas.
- Listas de correo dinámicas (suscriptores públicos).
