# [Centro Meteorológico Provincial Camagüey](https://web.cmw.insmet.cu)

Código abierto **[Centro Meteorológico Provincial Camagüey](https://web.cmw.insmet.cu)** generado con python y django. **[Tabler](https://tabler.io/)** es una plantilla de administración de código abierto creada por la agencia Codecalm. Viene con los componentes básicos y el conjunto de páginas prediseñadas necesarias para sentar las bases de cualquier aplicación - Diseño proporcionado por `Codecalm`.

- 👉 [Centro Meteorológico Provincial Camagüey](https://web.cmw.insmet.cu) - `Página del producto`

<br />

### 👉 Environment

Crear un nuevo archivo `.env` usando la muestra `env.sample`. El significado de cada variable se puede encontrar a continuación: 

- `DEBUG`: si es `True`, la aplicación se ejecuta en modo de desarrollo
  - Para producción debe utilizarse `False`
- Para`MySql`
  - Instale el controlador de base de datos: `pip install mysqlclient` 
  - Crear una base de datos y asignar un nuevo usuario (derechos completos)
  - Edite `.env` para que coincida con la base de datos, el usuario, la contraseña .. 
- Para `PostgreSql`
  - Instale el controlador de base de datos: `pip install psycopg2-binary` 
  - Crear una base de datos y asignar un nuevo usuario (derechos completos)
  - Edite `.env` para que coincida con la base de datos, el usuario, la contraseña .. 

<br />

### 👉 Construcción manual

> Descargar el código

```bash
$ git clone https://github.com/yoelvismr/web-cmw-insmet-cu.git
$ cd web-cmw-insmet-cu
```

<br />

### 👉 Configurar para `Unix`, `MacOS` 

> Instale módulos a través de `VENV`  

```bash
$ virtualenv .venv
$ source .venv/bin/activate
$ pip3 install -r requirements.txt
```

<br />

> Configurar la base de datos

```bash
$ python manage.py makemigrations
$ python manage.py migrate
$ python manage.py collectstatic --link --no-input
```

<br />

> Inicie la aplicación

```bash
$ python manage.py createsuperuser # Crear el administrador
$ python manage.py runserver       # Iniciar el proyecto
```

En este punto, la aplicación se ejecuta en `http://127.0.0.1:8000/`. 

<br />

### 👉 Configurar para `Windows` 

> Instale módulos a través de `VENV` (windows) 

```bash
$ python -m venv .venv
$ .venv\Scripts\activate
$ pip install -r requirements.txt
```

<br />

> Configurar la base de datos

```bash
$ python manage.py makemigrations
$ python manage.py migrate
```

<br />

> Cargar las estaciones en la base de datos

```bash
$ python stations_add.py
```

<br />

> Inicie la aplicación

```bash
$ python manage.py createsuperuser # Crear el administrador
$ python manage.py runserver       # Iniciar el proyecto
```

En este punto, la aplicación se ejecuta en `http://127.0.0.1:8000/`. 

<br />

### 👉 Deploy

> Instale y configure Nginx

- Instala `Nginx`: `sudo apt install nginx`

- Comentar el contenido del archivo `/etc/nginx/sites-available/default`

> Configuración nginx

```bash
$ nano /etc/nginx/sites-available/webcmp.conf
```

```bash
 upstream webcmpconn {
    server unix:/tmp/gunicorn-webcmp.sock fail_timeout=0;
 }

 server {
    listen 80;
    server_name web.cmw.insmet.cu;

    access_log /var/www/web-cmw-insmet-cu/logs/nginx-access.log;

    error_log /var/www/web-cmw-insmet-cu/logs/nginx-error.log;

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
         proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
         proxy_set_header Host $http_host;
         proxy_redirect off;
         proxy_pass http://webcmpconn;
    }

    error_page 500 502 503 504 /templates/500.html;
}
```

<br />

> Instale y configure Gunicorn
 
- Instala `Gunicorn`: `pip install gunicorn`

> Configuración gunicorn.sh

```bash
$ nano /pon aqui la ruta del gunicorn
```

```bash
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

exec ${DJANGODIR}/venv/bin/gunicorn ${DJANGO_WSGI_MODULE}:application \
  --name $NAME \
  --workers $NUM_WORKERS \
  --user=$USER --group=$GROUP \
  --bind=unix:$SOCKFILE \
  --log-level=debug \
  --log-file=$LOGDIR
```

<br />

> Instale y configure Supervisor

- Instala`Supervisor`: `pon aqui el comando pa instalar esto `

> Configuración supervisor

```bash
$ nano /etc/supervisor/conf.d/webcmp.conf
```

```bash
[program:webcmp]
command=/var/www/web-cmw-insmet-cu/gunicorn.sh
autostart=true
autorestart=true
stderr_logfile=/var/www/web-cmw-insmet-cu/logs/err.log
stdout_logfile=/var/www/web-cmw-insmet-cu/logs/out.log
user=root
```

En este punto, el producto debe estar en linea.

<br />
