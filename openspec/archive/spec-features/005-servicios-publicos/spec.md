# 005 · Servicios públicos

**Estado:** implementado ✅

## Qué hace

Listado público de servicios meteorológicos gratuitos ofrecidos por el centro. Los servicios públicos tienen título, resumen, y archivo PDF descargable. Se muestran en una página pública paginada con visor PDF embebido (PDF.js).

## Por qué

El centro ofrece servicios gratuitos (boletines, reportes, etc.) que deben ser accesibles al público general sin autenticación. Separar servicios públicos de comerciales evita confusión en la navegación.

## Criterios de aceptación

- [x] Listado público de servicios con `service_type='public'`, ordenado por fecha.
- [x] Paginación (10 por página).
- [x] Visor PDF embebido con PDF.js para cada servicio.
- [x] Acceso sin autenticación.
- [x] CRUD en dashboard para gestionar servicios (crear, editar, eliminar) con permisos.
- [x] Validación: servicios públicos requieren PDF; servicios comerciales requieren imagen + código + precio.

## Fuera de alcance

- Servicios comerciales con suscripción y pago (feature 006).
- Categorización o búsqueda avanzada de servicios.
