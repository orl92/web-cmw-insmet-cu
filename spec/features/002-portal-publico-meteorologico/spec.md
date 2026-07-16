# 002 · Portal público meteorológico

**Estado:** implementado ✅

## Qué hace

Conjunto de páginas públicas que muestran información meteorológica actualizada: tiempo hoy, tiempo mañana, comentario del tiempo, nota meteorológica, y avisos (alertas tempranas, ciclones tropicales, tormentas). Cada sección tiene una vista pública de detalle/listado y un panel administrativo CRUD con generación de PDF y notificaciones por correo.

## Por qué

Es la razón de ser del portal: proveer información meteorológica verificada al público camagüeyano. Los meteorólogos necesitan un dashboard para crear y gestionar estos contenidos, y el público necesita verlos sin autenticarse.

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

## Fuera de alcance

- Pronósticos detallados por región y período (feature 003).
- Mapas de modelos numéricos e imágenes satelitales (feature 004).
