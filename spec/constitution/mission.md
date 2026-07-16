# Misión

## Qué construimos

Sistema web del Centro Meteorológico Provincial Camagüey (CMP Camagüey). Un portal público meteorológico y un panel administrativo para la gestión de pronósticos, avisos, servicios comerciales, facturación y publicaciones científicas del instituto.

1. **Portal público** — tiempo actual, pronósticos (3 regiones + 5 días), modelos numéricos, imágenes satelitales, avisos meteorológicos, servicios públicos y comerciales.
2. **Dashboard administrativo** — CRUD completo de pronósticos, avisos, estaciones, clientes, servicios, suscripciones, facturación, publicaciones científicas y configuración del sitio.
3. **API REST** — exposición de estaciones, observaciones y pronósticos para integración con terceros.

## Para quién

- **Público general** — información meteorológica actualizada de la provincia Camagüey.
- **Meteorólogos del CMP** — creación y gestión de pronósticos, avisos y reportes.
- **Clientes comerciales** — suscripción a servicios meteorológicos, facturación y certificados.
- **Administradores del sistema** — gestión de usuarios, roles, configuración y modo mantenimiento.

## Principios

- **Un solo frontend** — toda la UI usa Django Templates + Tabler; sin frameworks JS separados.
- **Español primero** — toda la interfaz, verbose_name, mensajes y documentación están en español.
- **Archivos auto-gestionados** — los PDFs e imágenes se limpian automáticamente al actualizar o eliminar mediante `FileHandlerMixin`.
- **Permisos explícitos** — ningún modelo del dashboard asume permisos por defecto; se definen tuplas personalizadas de 4 permisos.

## Qué NO es

- Una SPA o aplicación con frontend desacoplado (React/Vue/Angular).
- Una plataforma de redes sociales o foro.
- Un sistema de código abierto genérico; está diseñado específicamente para el CMP Camagüey.
