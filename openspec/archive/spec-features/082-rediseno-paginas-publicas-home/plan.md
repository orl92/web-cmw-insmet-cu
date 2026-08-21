# 082 — plan

## Objetivo
Redisenar las paginas de contenido publico de la app `home` como documentos claros (PDF embebido como pieza central) y consolidar la duplicacion en partials reutilizables, manteniendo Tabler y el accessor `user.commercial_customer`.

## Decisiones previas
- No hay cambios de modelo/migraciones; solo templates + partials nuevos (+ ajustes menores de JS disparador).
- El partial `pdf_scripts` puede tomar un `pdf_url` opcional; la variante de listas (modal-only) hereda el handler de clics por `[data-pdf-url]`.
- `warning_type` colores: early=amarillo, storm=naranja, tropical_cyclone=azul.
- Orden por fases que evita tocar 2 veces el mismo archivo.

## Fases (secuenciadas)
1. **Fase A — base de partials compartidos** (task 1): crear `pdf_scripts`, `empty_free`, `pagination`, `form_utc_fields`. Aplicar paginacion Tabler y campos UTC en sus paginas.
2. **Fase B — articulo/PDF** (tasks 2-4): `weather_article` partial + PDF embebido; migrar hoy/manana/comentario/nota; modal con descarga.
3. **Fase C — avisos** (task 5): card por `warning_type`, alert-important, PDF embebido.
4. **Fase D — publicaciones** (tasks 6-7): grid destacada + cards; limpiar init PDFViewer muerto.
5. **Fase E — markup/a11y y servicios** (tasks 8-11): hrefs, h1→h2, estilos inline, onclick/alert, static'', qr duplicado, aria satelites. Aplicar `user.commercial_customer` ya corregido.
6. **Verificacion** (task 12): check, suite, render 200.
7. **Docs** (task 13): roadmap + commit descriptivo (082).
