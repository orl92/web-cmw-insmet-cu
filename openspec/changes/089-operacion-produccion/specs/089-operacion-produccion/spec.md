## Criterios de aceptación

- [ ] `pip install -r requirements.txt` instala whitenoise y gunicorn; `PRODUCTION=true` no crashea.
- [ ] `SECURE_PROXY_SSL_HEADER` configurado; cookies seguras funcionan tras proxy (verificable con `request.is_secure()` en un test con `HTTP_X_FORWARDED_PROTO=https`).
- [ ] Tareas Huey registradas: `huey_consumer` loguea las tareas al arrancar (o test de import en `ready()`).
- [ ] Sin `.env` con `PRODUCTION` set → `ImproperlyConfigured` con mensaje claro; sin `.env` en dev → sigue funcionando con secret aleatorio.
- [ ] `gunicorn.sh` no usa root.
- [ ] `python manage.py check` y `python manage.py test` pasan.
