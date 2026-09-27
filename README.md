# Centro Meteorológico Provincial Camagüey

[![Django](https://img.shields.io/badge/Django-5.2+-green.svg)](https://www.djangoproject.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Sistema web del **Centro Meteorológico Provincial Camagüey** desarrollado con Python/Django. Utiliza la plantilla **[Tabler](https://tabler.io/)** para la interfaz de administración.

🔗 **Sitio en producción**: [https://web.cmw.insmet.cu](https://web.cmw.insmet.cu)

## 🚀 Características principales

- Panel administrativo moderno con Tabler
- Configuración automática para entornos de desarrollo/producción
- Base de datos configurable (MySQL/PostgreSQL)
- Sistema de estaciones meteorológicas integrado
- Despliegue optimizado con Nginx + Gunicorn

## ⚙️ Configuración del entorno

El sistema detecta automáticamente el entorno (development/production) y configura las variables apropiadas:

### 🔄 Comparación de entornos

| Variable               | Desarrollo (`runserver`)            | Producción (`PRODUCTION=true`)              |
| ---------------------- | ------------------------------------- | ---------------------------------------------- |
| `DEBUG`              | `True` (activado)                   | `False` (desactivado)                        |
| `DB_ENGINE`          | `sqlite3` (automático)             | `postgresql`/`mysql` (requiere config)     |
| `EMAIL_BACKEND`      | Consola (emails en terminal)          | SMTP real (configuración obligatoria)         |
| `ALLOWED_HOSTS`      | `localhost,127.0.0.1` (automático) | Dominio real (requiere configuración)         |
| `EXTERNAL_HOSTNAME`  | No requerido                          | **Obligatorio** (dominio de producción) |
| `SECRET_KEY`         | Generada automáticamente             | Generada automáticamente                      |
| Configuración inicial | Completa automáticamente `.env`    | Genera plantilla `.env` para completar       |
| Base de datos          | SQLite (configuración cero)          | PostgreSQL/MySQL (configuración manual)       |
| Archivos estáticos    | Servidos por Django                   | Servidos por Nginx + Whitenoise                |
| Panel de errores       | Detallado (con stack traces)          | Seguro (páginas de error personalizadas)      |

**Key Features por entorno:**

- **Desarrollo**:

  - Configura todo automáticamente al ejecutar `runserver`
  - No requiere configuración manual inicial
  - Incluye herramientas de depuración
- **Producción**:

  - Genera plantilla `.env` al ejecutar `python manage.py generate_env --production` con valores requeridos
  - Exige validación manual de configuraciones críticas
  - Habilita optimizaciones de seguridad y performance

## 🛠️ Instalación

### Requisitos previos

- Python 3.14 (todos los jobs de CI fijan `python-version: "3.14"` y ruff apunta a `py314`)
- pip
- virtualenv (recomendado)
- Instalar dependencias necesarias
```bash
sudo apt install libcairo2-dev pkg-config python3-dev wkhtmltopdf
```

### 1. Clonar el repositorio

```bash
git clone https://github.com/orl92/web-cmw-insmet-cu.git
cd web-cmw-insmet-cu
```

### 2. Configurar el entorno (un solo comando)

El `Makefile` deja el proyecto listo: crea el venv, instala las dependencias de
desarrollo y de tests, y activa los hooks de git.

```bash
make setup
```

<details>
<summary>Equivalente manual (si no usas <code>make</code>)</summary>

# Unix/MacOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

# Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

</details>

### 3. Dependencias — un archivo por entorno

Cada entorno se instala con **un solo archivo**. Todos están en `requirements/` y
son autocontenidos (cada uno incluye `base.txt` con `-r base.txt`).

| Archivo | Qué instala |
| --- | --- |
| `requirements/base.txt` | Runtime de la app. Sin gunicorn ni herramientas de desarrollo. |
| `requirements/dev.txt` | `base.txt` + tooling: ruff, bandit, pip-audit, djlint, pre-commit, django-debug-toolbar, setuptools, wheel. |
| `requirements/test.txt` | `base.txt` + django-debug-toolbar. |
| `requirements/prod.txt` | `base.txt` + gunicorn (servidor WSGI). |

```bash
pip install -r requirements/base.txt    # solo runtime
pip install -r requirements/dev.txt     # desarrollo (make setup)
pip install -r requirements/test.txt    # solo correr tests
pip install -r requirements/prod.txt    # producción
```

> `django-debug-toolbar` aparece en `dev.txt` **y** en `test.txt` a propósito: es una
> herramienta de desarrollo (`DEBUG=True`), pero `apps/core/tests/test_debug_toolbar.py`
> afirma que está instalada y en CI corre con `DEBUG=False`. Nunca va en `base.txt`:
> eso mandaría una dependencia de desarrollo a producción.

### 4. Configuración inicial de base de datos

```bash
python manage.py makemigrations
python manage.py migrate
$ python manage.py collectstatic --link --no-input
```

### 5. Cargar datos de estaciones

```bash
python manage.py add_stations_data
```

### 6. Crear usuario administrador

```bash
python manage.py createsuperuser
```

### 7. Iniciar la aplicación

```bash
# Modo desarrollo
python manage.py runserver
```

```bash
# Modo producción (pruebas locales)
PRODUCTION=true python manage.py runserver
```

En este punto, la aplicación se ejecuta en `http://127.0.0.1:8000/`.

## 🪝 Git hooks

Los hooks de pre-commit (ruff, djlint, detect-secrets) viajan **versionados** en
`.githooks/pre-commit`. Git no tiene hook de `clone`, así que activarlos es un comando:

```bash
make hooks    # equivalente a: git config core.hooksPath .githooks
```

`make setup` ya lo hace. El hook prefiere el binario del venv del repo
(`$root/.venv/bin/pre-commit`) y cae a `PATH`, por lo que funciona **sin activar el venv**.

> **⚠️ `pre-commit install` y `core.hooksPath` son mutuamente excluyentes.** `core.hooksPath`
> hace que git ignore `.git/hooks` por completo, así que correr ambos te deja depurando un
> hook que git nunca invoca. `make setup` corre `pre-commit install --install-hooks` **solo**
> para poblar los entornos de los hooks (descargados desde PyPI en la primera ejecución); la
> activación la hace `core.hooksPath`. Por eso se usa SIEMPRE `--install-hooks`: sin él, un
> fallo de red en el primer commit puede colgar el commit y perder el patch temporal de
> pre-commit con tus archivos modificados sin stagear.

Para correr los hooks manualmente sobre todo el repo:

```bash
.venv/bin/pre-commit run --all-files
```

## 🚀 Despliegue en Producción

### Configuración recomendada

- Nginx como proxy inverso
- Gunicorn como servidor de aplicaciones
- Supervisor para gestión de procesos

### 1. Configurar Nginx

```ini
sudo apt install nginx
sudo nano /etc/nginx/sites-available/webcmp.conf
```

#### Ejemplo de configuración:

```ini
proxy_cache_path /cache/nginx/tmpfs levels=1:2 keys_zone=webcmp:100m max_size=100m inactive=3h use_temp_path=off;

upstream web.cmw.insmet.cu {
    server unix:/tmp/gunicorn-webcmp.sock fail_timeout=0;
}

server {
        listen 80 default_server;
        listen [::]:80 default_server;
        server_name _;
        return 301 https://$host$request_uri;
}

server {
    listen 443 ssl default_server;
    listen [::]:443 ssl default_server;
    ssl_certificate /etc/nginx/certificate/web.cmw.insmet.cu.crt;
    ssl_certificate_key /etc/nginx/certificate/web.cmw.insmet.cu.key;
    server_name web.cmw.insmet.cu;
    access_log /var/www/web-cmw-insmet-cu/logs/nginx-access.log;
    error_log /var/www/web-cmw-insmet-cu/logs/nginx-error.log;

    # Agrega estos headers esenciales
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header Host $http_host;
    proxy_redirect off;

    # Configuraci  n de timeout
    proxy_read_timeout 300s;
    proxy_connect_timeout 75s;

    location /media/  {
        alias /var/www/web-cmw-insmet-cu/media/;
    }

    location /static/ {
        alias /var/www/web-cmw-insmet-cu/staticfiles/;
    }

    location /static/admin/ {
        alias /var/www/web-cmw-insmet-cu/staticfiles/admin/;
    }

    location / {
         proxy_pass http://web.cmw.insmet.cu;

         # Espec  ficamente para Django
         proxy_set_header Upgrade $http_upgrade;
         proxy_set_header Connection "upgrade";
    }

    error_page 500 502 503 504 /templates/500.html;
}
```

> **Cookies seguras tras el proxy:** Django ahora lee `SECURE_PROXY_SSL_HEADER`
> (`X-Forwarded-Proto`) en producción, por lo que `request.is_secure()` se
> resuelve como `True` detrás de Nginx y las cookies de sesión/CSRF seguras se
> envían correctamente. Mantenga `proxy_set_header X-Forwarded-Proto $scheme;`
> en la configuración de Nginx (arriba); no lo elimine.

#### Comentar el contenido de:

```ini
/etc/nginx/sites-available/default
```

### 2. Configurar Gunicorn

```ini
pip install -r requirements/prod.txt
nano gunicorn.sh
```

> `requirements/prod.txt` ya **incluye gunicorn** (es `base.txt` + gunicorn), así que
> no hace falta un `pip install gunicorn` aparte.

#### Ejemplo de configuración:

```ini
#!/bin/bash
NAME="webcmp"
DJANGODIR=$(cd `dirname $0` && pwd)
SOCKFILE=/tmp/gunicorn-webcmp.sock
LOGDIR=${DJANGODIR}/logs/gunicorn.log
# El servicio NO debe correr como root. El usuario dedicado (webcmp) debe ser
# el propietario del venv (o ejecutar ./gunicorn.sh como ese usuario) para poder
# escribir el socket y servir estáticos/media.
USER=${GUNICORN_USER:-webcmp}
GROUP=${GUNICORN_GROUP:-webcmp}
NUM_WORKERS=5
DJANGO_WSGI_MODULE=config.wsgi

rm -frv $SOCKFILE

echo $DJANGODIR

cd $DJANGODIR

exec ${DJANGODIR}/.venv/bin/gunicorn ${DJANGO_WSGI_MODULE}:application \
  --name $NAME \
  --workers $NUM_WORKERS \
  --user=$USER --group=$GROUP \
  --bind=unix:$SOCKFILE \
  --log-level=debug \
  --log-file=$LOGDIR
```

> **Usuario no-root:** cree el usuario dedicado y asígnele la propiedad de los
> directorios que Gunicorn necesita escribir:
> ```bash
> useradd -r -s /bin/false webcmp
> chown -R webcmp:webcmp /var/www/web-cmw-insmet-cu/.venv \
>   /var/www/web-cmw-insmet-cu/media \
>   /var/www/web-cmw-insmet-cu/staticfiles \
>   /var/www/web-cmw-insmet-cu/logs
> ```

## 3. Configurar Supervisor

```bash
sudo nano /etc/supervisor/conf.d/webcmp.conf
```

#### Ejemplo de configuración:

```ini
[program:webcmp]
command=/var/www/web-cmw-insmet-cu/gunicorn.sh
directory=/var/www/web-cmw-insmet-cu
user=webcmp
autostart=true
autorestart=true
stderr_logfile=/var/log/webcmp.err.log
stdout_logfile=/var/log/webcmp.out.log
```

### 4. Configurar Huey Worker

El worker de Huey procesa las tareas asíncronas (envío de correos y generación de PDFs). Se ejecuta como un proceso separado de Gunicorn.

```bash
huey_consumer.py config.huey.huey
```

#### Supervisor (recomendado)

Agregar un segundo programa en `/etc/supervisor/conf.d/webcmp.conf`:

```ini
[program:webcmp-huey]
command=/var/www/web-cmw-insmet-cu/.venv/bin/huey_consumer.py config.huey.huey
directory=/var/www/web-cmw-insmet-cu
user=webcmp
autostart=true
autorestart=true
stderr_logfile=/var/log/webcmp-huey.err.log
stdout_logfile=/var/log/webcmp-huey.out.log
```

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start webcmp-huey
```

## 🤝 Cómo Contribuir

- Haz un fork del proyecto
- Crea una rama para tu feature (git checkout -b feature/nueva-funcionalidad)
- Haz commit de tus cambios (git commit -am 'Añade nueva funcionalidad')
- Haz push a la rama (git push origin feature/nueva-funcionalidad)
- Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Ver LICENSE para más detalles.

Centro Meteorológico Provincial Camagüey
Instituto de Meteorología de Cuba
© 2025
