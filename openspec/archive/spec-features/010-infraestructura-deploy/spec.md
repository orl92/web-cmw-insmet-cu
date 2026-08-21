# 010 · Infraestructura y deploy

**Estado:** implementado ✅

## Qué hace

Configuración del entorno de desarrollo y producción: auto-generación de `.env` con SECRET_KEY cifrada (Fernet), detección automática de modo (dev/prod), base de datos SQLite en desarrollo y PostgreSQL/MySQL con SSL en producción, WhiteNoise para estáticos en producción con `CompressedManifestStaticFilesStorage`, Gunicorn con socket Unix, y validación de configuración al arrancar en modo producción.

## Por qué

Sin infraestructura no hay deploy. El sistema debe funcionar con `python manage.py runserver` en desarrollo y con Nginx+Gunicorn+Supervisor en producción, minimizando la configuración manual y evitando exponer secretos.

## Criterios de aceptación

- [x] `.env` se auto-genera al arrancar si no existe con plantilla para dev o prod.
- [x] SECRET_KEY se genera aleatoriamente, se cifra con Fernet y se almacena cifrada en `.env`.
- [x] `python manage.py runserver` → DEBUG=True, SQLite, consola email.
- [x] `python manage.py runserver --production` → DEBUG=False, valida DB/email/LDAP.
- [x] WhiteNoise con `CompressedManifestStaticFilesStorage` en producción; servido por Nginx en `/static/`.
- [x] Gunicorn con 5 workers, socket Unix `/tmp/gunicorn-webcmp.sock`.
- [x] WSGI: `config.wsgi:application`.
- [x] Soporte SSL para PostgreSQL (sslmode, sslrootcert) y MySQL (ssl_mode).

## Fuera de alcance

- Configuración de CI/CD.
- Contenedores Docker.
- Orquestación (Kubernetes, Swarm).
- Monitoring y alertas.
