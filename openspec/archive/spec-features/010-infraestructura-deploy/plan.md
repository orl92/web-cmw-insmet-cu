# 010 · Infraestructura y deploy — Plan

## Enfoque

Toda la lógica de infraestructura vive en `config/settings.py`: auto-detección de modo, auto-generación de `.env`, cifrado Fernet, selección de BD, WhiteNoise dinámico. Script Gunicorn separado. Nginx/Supervisor configurados externamente.

## Implementación

1. **Auto-generación `.env`**: `create_default_env(production=False)` al importar settings. Genera SECRET_KEY → cifra con Fernet → escribe `.env`.
2. **Detección modo**: `IS_PRODUCTION = 'PRODUCTION' in os.environ or '--production' in sys.argv`.
3. **Fernet**: `encryption_key = Fernet.generate_key()`, `cipher_suite = Fernet(encryption_key)`, `decrypt_secret_key()` inversa.
4. **BD**: SQLite si dev, PostgreSQL/MySQL vía env vars si prod. `CONN_MAX_AGE=600`.
5. **WhiteNoise**: insertado en MIDDLEWARE solo si `IS_PRODUCTION`. STATICFILES_STORAGE condicional.
6. **Gunicorn**: `gunicorn.sh` con 5 workers, socket Unix, logs.
7. **Validación**: `validate_environment()` y `validate_database_config()` en producción.

## Decisiones

- **Fernet vs hash simple** — Fernet permite descifrar la SECRET_KEY en tiempo de ejecución sin almacenarla en texto plano. Es un cifrado simétrico con clave única.
- **Auto-generación de `.env`** — elimina el paso manual de crear el archivo; el desarrollador solo ejecuta `runserver`.
- **WhiteNoise dinámico** — en desarrollo no se necesita (Django static serve es suficiente); en producción da caching y compresión.
- **Nginx/Supervisor fuera del repo** — son específicos del servidor; el repo solo contiene la app y su script Gunicorn.

## Riesgos

- **Fernet key perdida** — si se pierde ENCRYPTION_KEY, la SECRET_KEY es irrecuperable. Se respalda `.env`.
- **wkhtmltopdf faltante** — necesario para pdfkit (facturación). Se documenta en setup.
