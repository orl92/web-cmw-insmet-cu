# 018 · Vistas de Certificados y Contratos

**Estado:** planificado

## Qué hace

Agrega vistas CRUD y entradas en el menú del dashboard para los modelos `Contract` y `Certificate`. Actualmente solo se crean automáticamente durante el flujo de facturación/aprobación.

## Criterios de aceptación

- [ ] Contract: ListView, CreateView, DetailView, DeleteView (POST-only modal)
- [ ] Certificate: ListView, DetailView (descarga PDF), DeleteView
- [ ] Entradas en menú sidebar
- [ ] URLs `/dashboard/contratos/` y `/dashboard/certificados/`
- [ ] Flujo existente de facturación/aprobación no se rompe
- [ ] `python manage.py test` — todos pasan
