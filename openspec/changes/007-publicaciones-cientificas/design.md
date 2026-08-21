# 007 · Publicaciones científicas — Plan

## Enfoque

Dos modelos (ScientificPublication, Author) con relación FK + M2M para coautores. Inline formset para gestión de coautores. Deduplicación en save. PDF generado con xhtml2pdf.

## Implementación

1. **Modelos**: `Author` (first_name, last_name, email, institution, orcid_id), `ScientificPublication` (title, author FK, coauthors M2M, publication_date, summary, pdf_file). Ambos con permisos custom.
2. **Formularios**: `ScientificPublicationForm` + `CoauthorForm`. Helper `get_coauthor_formset()` para formset inline.
3. **Vistas**: ListView, CreateView, UpdateView (solo superuser), DeleteView (POST), DetailView, PDFView. Logging con `log_action`.
4. **Deduplicación**: `get_or_create` por email, o por first_name+last_name si no hay email.

## Decisiones

- **Deduplicación por email** — evita crear el mismo autor两次; fallback a nombre+apellido.
- **xhtml2pdf para PDF de publicación** — consistente con el resto del sistema (Weather PDFs usan xhtml2pdf).
- **Update solo superuser** — las publicaciones son registros sensibles; solo administradores pueden modificarlas una vez creadas.

## Riesgos

- **Coautores duplicados** — mitigado con get_or_create y validación en el formset.
- **PDF grande** — FileHandlerMixin asegura limpieza al reemplazar o eliminar.
