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

| Variable               | Desarrollo (`runserver`)            | Producción (`runserver --production`)       |
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

  - Genera plantilla `.env` al ejecutar `runserver --production` con valores requeridos
  - Exige validación manual de configuraciones críticas
  - Habilita optimizaciones de seguridad y performance

## 🛠️ Instalación

### Requisitos previos

- Python 3.8+
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

### 2. Configurar entorno virtual

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

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

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
python manage.py runserver --production
```

En este punto, la aplicación se ejecuta en `http://127.0.0.1:8000/`.

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

#### Comentar el contenido de:

```ini
/etc/nginx/sites-available/default
```

### 2. Configurar Gunicorn

```ini
pip install gunicorn
nano gunicorn.sh
```

#### Ejemplo de configuración:

```ini
#!/bin/bash
NAME="webcmp"
DJANGODIR=$(cd `dirname $0` && pwd)
SOCKFILE=/tmp/gunicorn-webcmp.sock
LOGDIR=${DJANGODIR}/logs/gunicorn.log
USER=root
GROUP=root
NUM_WORKERS=5
DJANGO_WSGI_MODULE=core.wsgi

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

## 3. Configurar Supervisor

```bash
sudo nano /etc/supervisor/conf.d/webcmp.conf
```

#### Ejemplo de configuración:

```ini
[program:webcmp]
command=/var/www/web-cmw-insmet-cu/gunicorn.sh
directory=/var/www/web-cmw-insmet-cu
user=root
autostart=true
autorestart=true
stderr_logfile=/var/log/webcmp.err.log
stdout_logfile=/var/log/webcmp.out.log
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
