# Spec — 007-publicaciones-cientificas

## Criterios de aceptación

- [x] CRUD completo de publicaciones científicas (list, create, update, delete, detail).
- [x] CRUD de autores con ORCID opcional.
- [x] Coautores gestionados con inline formset (add/delete).
- [x] Deduplicación de autores por email o nombre+apellido.
- [x] Generación de PDF con xhtml2pdf desde template.
- [x] Permisos: CRUD con `dashboard.*_scientific_publication`; update solo superuser.
- [x] Limpieza automática de PDF con FileHandlerMixin.
