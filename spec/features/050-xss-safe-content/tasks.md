# Tasks — Feature 050

- [ ] Verificar si `home/templatetags/` existe, si no crearlo
- [ ] Crear filtro `sanitize_html` en `home/templatetags/safe_filters.py`
- [ ] `tiempo_h.html` - Reemplazar `|safe` por `|sanitize_html`
- [ ] `tiempo_m.html` - Reemplazar `|safe` por `|sanitize_html`
- [ ] `comentario_tiempo.html` - Reemplazar `|safe` por `|sanitize_html`
- [ ] `nota_meteorologica.html` - Reemplazar `|safe` por `|sanitize_html`
- [ ] `python manage.py check` — sin errores
- [ ] `python manage.py test home` — tests pasan
