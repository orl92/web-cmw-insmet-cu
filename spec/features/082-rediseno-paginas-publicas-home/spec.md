# 082 — rediseno-paginas-publicas-home

## Motivacion

Las paginas de contenido publico de la app `home` (El Tiempo hoy/manana, Comentario del Tiempo, Nota Meteorologica, Avisos, Publicaciones Cientificas) muestran el boletin como un "cartelon": un `<h1>` centrado, una linea "Departamento de Pronosticos", 2 textos de fecha/hora y un boton "Ver PDF". El contenido real vive en el PDF, pero la pagina lo trata como accesorio: se ve vacia, sin jerarquia, sin informacion util a la vista (vigencia, autor, tipo de aviso) y con una identidad identica entre tipos. Ademas hay duplicacion alta de boilerplate PDF/estado-vacio/campos UTC/paginacion.

**Objetivo**: redisenar estas paginas como *documentos/articulos* que entregan el boletin de forma clara y atractiva (PDF embebido como pieza central), y consolidar la duplicacion en partials reutilizables.

## Fundamentos

- UI: exclusivamente Tabler.io (Bootstrap 5). Referencias usadas: `cards` (header/footer/stamp/status), `ribbons`, `alerts` (important/filled), `datagrid`, `page-header`, `empty-state`, paginacion Tabler (`ul.pagination`).
- Elemento firma: **visor de PDF embebido** con barra de acciones, no un boton flotante.
- `warning_type` del modelo (`apps/meteo/models.py:241`): `early`/`storm`/`tropical_cyclone` → estilos de aviso distintos.

## Alcance — Rediseno de paginas de contenido

### Tiempo hoy / manana / Comentario / Nota (partial `weather_article`)
1. `page-header` con pre-title ("El Tiempo · Pronostico del Dia") + titulo `h2` + chip de vigencia.
2. Metadata en **datagrid** Tabler con iconos (Fecha, Hora/Vigencia, Autor).
3. **PDF embebido** (altura fluida, borde, barra superior: titulo + "Descargar PDF" + "Pantalla completa").
4. Footer con avatar + autor + hora de publicacion.
5. Estado vacio con partial `empty_state`.

### Avisos (partial `warnings`/uso de `warning_type`)
6. Card con `ribbon` / `card-status` segun tipo: `early`→amarillo, `storm`→naranja, `tropical_cyclone`→azul.
7. `alert-important` de cabecera + datagrid valido-hasta + resumen + PDF embebido + boton secundario.

### Publicaciones Cientificas
8. Entrada destacada (ultima) + grid de cards (icono/portada PDF, autor, fecha, institucion, "Leer PDF" / "Descargar").

## Alcance — DRY (consolidar duplicacion)

- **D1** `includes/home/pdf_scripts.html`: config worker + init PDFViewer + handler de clics del modal (param opcional `pdf_url`). Reemplaza el boilerplate en ~7 archivos.
- **D2** Partial de estado vacio reutilizable (basado en `empty_state.html`), reemplaza el bloque `boy-refresh.webp` repetido en ~6 paginas.
- **D3** `includes/home/weather_article.html` (apuntala el rediseno del bloque 1-5).
- **D4** `includes/home/form_utc_fields.html`: campo Fecha+Hora UTC (+ municipio/variable opcional) para `models/maps`, `models/meteogram`, `models/sounding`.
- **D5** `includes/pagination.html` con paginacion **Tabler** (`ul.pagination`) para `services/public` y `services/commercial`.

## Alcance — Bugs / markup / accesibilidad

- **V7** `institution/publications.html`: quitar init de `PDFViewer` para contenedores `pdfPreviewContainer-N` que no existen en su markup (JS muerto).
- **V1** `<a>` sin `href` (tiulo/resumen) en `services/public` y `services/commercial` → `h3`/`p` reales.
- **V2** Jerarquia `<h1>`: el articulo usara `h2` (convive con `page-title`); evita multiples `h1` por pagina.
- **V3** Estilos inline recurrentes (`object-fit`, `height`, `max-width`, `display:none`) → utilidades/partial CSS.
- **V4** `onclick` inline + `alert()` en `models/maps` (toast) y `payment/qr` (`shareLink`) → listeners + `aria-live`.
- **V5** `{% static '' %}` y scripts comentados en `models/maps` y `models/meteogram`.
- **V6** `payment/qr`: marco desktop/movil duplicado; `aria-label` en imagenes satelitales (`satellites.html`).

## Fuera de alcance

- Refactor de `maps.js`, `qr.js`, `pdf-viewer.js` (solo ajustes de templates/JS disparador).
- Modificacion de vistas, modelos o URLs (excepto partials nuevos).
- La espec 081 cubre partials compartidos (footer, navbar, empty_state, forecast_region_card); aqui no se repite.

## Criterios de Aceptacion

1. Cada pagina de contenido (tiempo, comentario, nota, avisos, publicaciones) renderiza 200 por test client (con `ALLOWED_HOSTS` incluyendo `testserver`), con y sin datos.
2. El PDF aparece embebido con acciones "Descargar" y "Pantalla completa" (modal fullscreen mantiene controles).
3. Avisos diferenciados visualmente por `warning_type` (badge/ribbon/status).
4. Sin `<h1>` duplicado por pagina; metadata visible en datagrid; estado vacio consistente.
5. Eliminada la duplicacion de boilerplate PDF/estado-vacio/campos UTC/paginacion (partials compartidos).
6. Sin regresion en `user.commercial_customer` (fix B1 ya enviado queda intacto).
7. `python manage.py check` sin errores y suite completa OK.

## Notas de implementacion

- Fases (ver `tasks.md`) ordenadas para no reescribir el mismo archivo 2 veces.
- El acceso a usuario/cliente correcto es `user.commercial_customer` (no `user.customer`).
- Verificacion visual por render (test client) + revisar que no rompa estructura en desktop/movil.