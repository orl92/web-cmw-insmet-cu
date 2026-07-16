# 007 · Publicaciones científicas

**Estado:** implementado ✅

## Qué hace

Gestión de publicaciones científicas del instituto. Cada publicación tiene título, autor principal, coautores (con deduplicación), fecha, resumen y archivo PDF. Los autores tienen nombre, email, institución y ORCID. Incluye generación de PDF con xhtml2pdf y detalle con metadatos completos.

## Por qué

El centro genera publicaciones científicas que deben ser catalogadas y accesibles. El sistema permite a los investigadores gestionar su producción científica y al público consultarla.

## Criterios de aceptación

- [x] CRUD completo de publicaciones científicas (list, create, update, delete, detail).
- [x] CRUD de autores con ORCID opcional.
- [x] Coautores gestionados con inline formset (add/delete).
- [x] Deduplicación de autores por email o nombre+apellido.
- [x] Generación de PDF con xhtml2pdf desde template.
- [x] Permisos: CRUD con `dashboard.*_scientific_publication`; update solo superuser.
- [x] Limpieza automática de PDF con FileHandlerMixin.

## Fuente de alcance

- Indexación en Google Scholar o DOI minting.
- Exportación a BibTeX o Zotero.
- Módulo de revisión por pares.
