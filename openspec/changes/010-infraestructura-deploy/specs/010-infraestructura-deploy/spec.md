# Spec — 010-infraestructura-deploy

## Criterios de aceptación

- [x] `.env` se auto-genera al arrancar si no existe con plantilla para dev o prod.
- [x] SECRET_KEY se genera aleatoriamente, se cifra con Fernet y se almacena cifrada en `.env`.
- [x] `python manage.py runserver` → DEBUG=True, SQLite, consola email.
- [x] `python manage.py runserver --production` → DEBUG=False, valida DB/email/LDAP.
- [x] WhiteNoise con `CompressedManifestStaticFilesStorage` en producción; servido por Nginx en `/static/`.
- [x] Gunicorn con 5 workers, socket Unix `/tmp/gunicorn-webcmp.sock`.
- [x] WSGI: `config.wsgi:application`.
- [x] Soporte SSL para PostgreSQL (sslmode, sslrootcert) y MySQL (ssl_mode).
