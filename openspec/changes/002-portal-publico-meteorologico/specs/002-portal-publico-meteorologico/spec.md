# Spec — 002-portal-publico-meteorologico

## Criterios de aceptación

- [x] Página pública de tiempo hoy muestra el último registro del día desde `WeatherToday`.
- [x] Página pública de tiempo mañana muestra el último registro disponible.
- [x] Página pública de comentario del tiempo y nota meteorológica con mismo patrón.
- [x] Páginas públicas de avisos filtran solo los vigentes (`valid_until >= now`).
- [x] Dashboard CRUD completo (list, create, update, delete, detail) para cada modelo.
- [x] Generación de PDF con `xhtml2pdf` para WeatherToday, WeatherTomorrow, WeatherCommentary y WeatherNote.
- [x] Notificación por correo al crear/actualizar con archivo PDF adjunto.
- [x] Detección de cambios relevantes para evitar correos duplicados.
- [x] `FileHandlerMixin` para limpieza automática de PDFs al actualizar o eliminar.
