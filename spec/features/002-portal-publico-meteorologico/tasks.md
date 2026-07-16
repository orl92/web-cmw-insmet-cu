# 002 · Portal público meteorológico — Tareas

- [x] Crear modelos WeatherToday, WeatherTomorrow, WeatherCommentary, WeatherNote en dashboard/models.py.
- [x] Crear BaseWarning abstracta y modelos EarlyWarning, TropicalCyclone, StormWarning.
- [x] Crear modelo EmailRecipientList y EmailRecipient.
- [x] Implementar vistas públicas (home): IndexView, WeatherTodayDetailView, WeatherTomorrowDetailView, WeatherCommentaryDetailView, WeatherNoteDetailView.
- [x] Implementar vistas públicas de avisos: EarlyWarningListView, TropicalCycloneListView, StormListView.
- [x] Implementar vistas de dashboard (list, create, update, delete, detail) para WeatherToday, WeatherTomorrow.
- [x] Implementar vistas de dashboard para WeatherCommentary, WeatherNote.
- [x] Implementar vistas de dashboard para EarlyWarning, TropicalCyclone, StormWarning.
- [x] Implementar PDF views con xhtml2pdf.
- [x] Implementar mail_send() en dashboard/data/mail_send.py.
- [x] Integrar detección de cambios en create/update views.
- [x] Validar con `python manage.py check` y prueba manual.
