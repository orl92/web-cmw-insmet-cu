# Design — 017-public-pdf-blog

## Partial compartido (ya existe)
`document_card.html` (title/summary/publisher/date + botón "Ver PDF" → `#documentPdfModal`) y `document_pdf_modal.html` ( `<object>` nativo lazy + descarga). `document-modal.js` es idempotente (evita doble fetch). Reusar en todas partes; incluir el modal exactamente una vez por página.

## 1. Warning.title
Agregar `title = models.CharField(max_length=200, blank=True, null=True, verbose_name="Título")` a `Warning`. `makemigrations` + `migrate` (gitignored). La card pasa `title=warning.title|default:warning.summary`; se omite `summary` para no duplicar. El admin form muestra el campo.

## 2. avisos.html
- Quitar `badge=` y `title='Aviso meteorológico'`.
- `{% include 'includes/home/document_card.html' with title=warning.title|default:warning.summary publisher=warning.user.get_full_name date=warning.valid_until|date:'d/m/Y H:i' pdf_url=pdf_url pdf_title=warning.get_warning_type_display %}`
- Arreglar columna en blanco: el wrapper es `<div class="col-md">` sin `.row` padre. Cambiar a `<div class="col-12">` (o envolver en `<div class="row"><div class="col-12">`).

## 3. publications.html
Reemplazar la card custom (líneas ~7-65) con un loop `row row-deck`:
```
<div class="row row-deck">
  {% for object in objects %}
    <div class="col-sm-6 col-lg-4">
      {% include 'includes/home/document_card.html' with title=object.title summary=object.summary publisher=object.author date=object.publication_date pdf_url=object.pdf.url pdf_title=object.title %}
    </div>
  {% endfor %}
</div>
```
Eliminar el botón "Ver detalle" (`publications:public_detail`) y el bloque de email ofuscado. Mantener un solo `document_pdf_modal.html` tras el loop.

## 4. Home grid
Leer la plantilla home; envolver los bloques de render de avisos y publicaciones en grids `row row-deck` (col-sm-6 col-lg-4 / col-md-6) para mostrarlos como tarjetas blog. Preservar los encabezados de sección.

## 5. Remover public_detail
- Borrar `apps/publications/templates/pages/publications/public_detail.html`.
- Quitar `ScientificPublicationPublicDetailView` (+ su import) de `apps/publications/views.py`.
- Quitar la URL `<uuid:uuid>/public/` (name `public_detail`) de `apps/publications/urls.py`.
- Borrar `apps/publications/tests/test_public_detail.py`.
- grep `publications:public_detail` y eliminar referencias colgantes.

## 6. Dashboard sweep
En cada plantilla de detalle del dashboard, reemplazar el `<a target="_blank" ...>Ver PDF</a>` crudo (y su wrapper) con `{% include 'includes/home/document_card.html' with title=... pdf_url=... pdf_title=... %}` y agregar `{% include 'includes/home/document_pdf_modal.html' %}` una vez (si no está). Asegurar exactamente un `#documentPdfModal` por página.

## 7. Borrar assets muertos
Eliminar `static/dist/js/pdf-form-preview.js` y `static/dist/css/pdf-form-preview.css`. grep confirma cero referencias.

## 8. Tests
- Borrar `test_public_detail.py`.
- Actualizar cualquier test que afirme 'Aviso meteorológico' o 'Alerta Temprana' (cambiar a afirmar markup blog/document_card).
- Agregar/ajustar: card de avisos sin badge + título=summary; lista de publicaciones usa document_card en grid y sin link public_detail; detalle de dashboard renderiza `#documentPdfModal` + botón.
- Correr `python manage.py test` (full) + djlint + check.
