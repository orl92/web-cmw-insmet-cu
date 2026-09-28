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

  - Genera el `.env` al ejecutar `python scripts/generate_env.py --production` con valores requeridos, y escribe la `ENCRYPTION_KEY` en un archivo aparte (600) que systemd carga con `EnvironmentFile=`
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

Guía para un servidor **nuevo**, en Ubuntu 26.04 LTS con Python 3.14 nativo. Si
estás manteniendo un servidor que ya corre, migrá desde
[Migrar desde supervisor](#migrar-desde-supervisor) al final de esta sección.

El stack es: **Nginx** (TLS, estáticos y media) → **Gunicorn** vía systemd →
**PostgreSQL**, más un worker de **Huey** aparte para correos y PDFs. Redis es
opcional: el caché por defecto corre en memoria del proceso.

Los tres archivos de configuración están versionados en `deploy/`. Son
**ejemplos deterministas, sin secretos**: lo que cambia por instalación son
rutas y rutas de certificado, y eso se edita en el servidor.

### 1. Preparar el sistema

```bash
sudo apt update
sudo apt install -y python3.14 python3.14-venv postgresql redis-server nginx

# Usuario dedicado. El servicio NUNCA corre como root.
sudo useradd -r -s /bin/false webcmp

sudo mkdir -p /srv/webcmp
sudo chown webcmp:webcmp /srv/webcmp
```

### 2. PostgreSQL

```bash
sudo -u postgres psql <<'SQL'
CREATE USER webcmp WITH PASSWORD 'CAMBIAR_ESTA_CLAVE';  -- pragma: allowlist secret
CREATE DATABASE webcmp OWNER webcmp;
\c webcmp
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT ALL ON SCHEMA public TO webcmp;
SQL
```

`psycopg[binary]` ya está en `requirements/prod.txt`; no se instala el driver a mano.

### 3. El código y el `.env`

```bash
sudo -u webcmp git clone <repo> /srv/webcmp
cd /srv/webcmp
sudo -u webcmp python3.14 -m venv .venv
sudo -u webcmp .venv/bin/pip install -r requirements/prod.txt
sudo -u webcmp .venv/bin/python manage.py migrate
sudo -u webcmp .venv/bin/python manage.py collectstatic --no-input
```

Ahora el paso que antes era imposible de hacer bien: **el `.env` se genera sin
Django arrancado**.

```bash
sudo -u webcmp .venv/bin/python scripts/generate_env.py --production
```

Eso escribe dos archivos:

| Archivo | Contiene | Permisos |
|---|---|---|
| `/srv/webcmp/.env` | `SECRET_KEY` cifrada, `DEBUG=False`, `DB_*`, SMTP, LDAP comentado | `600` |
| `/etc/webcmp/encryption.env` | `ENCRYPTION_KEY` (la clave de descifrado) | `600`, root |

**Por qué la `ENCRYPTION_KEY` no va en el `.env`:** si comparten archivo, un
`.env` filtrado entrega el secreto ya descifrado. La clave con la que se cifró
viaja junto al texto cifrado, así que no hay nada que descifrar. La clave de
descifrado tiene que vivir en un archivo que el `.env` no puede alcanzar, y
`systemd` lo carga con `EnvironmentFile=-`.

Después editá los `CHANGE_ME` del `.env` (correo SMTP y `DB_PASS`):

```bash
sudo -u webcmp nano /srv/webcmp/.env
```

Los permisos del archivo de clave, por si lo generaste antes de esto:

```bash
sudo chown root:root /etc/webcmp/encryption.env
sudo chmod 600 /etc/webcmp/encryption.env
```

Los directorios que el servicio tiene que poder escribir:

```bash
sudo mkdir -p /srv/webcmp/media /srv/webcmp/logs /srv/webcmp/staticfiles
sudo chown -R webcmp:webcmp /srv/webcmp/media /srv/webcmp/logs /srv/webcmp/staticfiles
```

### 4. systemd

```bash
sudo cp deploy/systemd/webcmp.service deploy/systemd/webcmp-huey.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now webcmp webcmp-huey
systemctl status webcmp webcmp-huey
```

Los logs van a journald, no a archivos:

```bash
journalctl -u webcmp -f
journalctl -u webcmp-huey -f
```

> **Los paths de `/srv/webcmp` están escritos en el `.service`, no en una
> variable.** En un unit, `APP_DIR=/srv/webcmp` no es una clave válida de
> systemd y `systemd-analyze verify` lo rechaza. Si el checkout vive en otro
> lugar, se cambian las rutas y se verifica:
> `systemd-analyze verify /etc/systemd/system/webcmp.service`.

> **`EnvironmentFile=-` lleva el guion a propósito.** Sin la clave de descifrado,
> el servicio arranca y falla con el error accionable de `load_secret_key()`,
> que dice qué comando ejecutar. Sin el guion, fallaría systemd con un error que
> no dice qué hacer. Si preferís que el fallo sea estricto, quitá el guion.

### 5. Nginx

```bash
sudo cp deploy/nginx/webcmp.conf.example /etc/nginx/sites-available/webcmp.conf
sudo nano /etc/nginx/sites-available/webcmp.conf   # certificados y rutas
sudo rm -f /etc/nginx/sites-enabled/default
sudo ln -s /etc/nginx/sites-available/webcmp.conf /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

> **No elimines `proxy_set_header X-Forwarded-Proto $scheme;`.** Django lo lee
> con `SECURE_PROXY_SSL_HEADER` para resolver `request.is_secure()`. Sin esa
> línea, las cookies de sesión seguras no se envían y el usuario entra en un
> bucle de logout.

### 6. Verificar

```bash
# Que los settings de producción cargan con la clave de descifrado del unit
sudo -u webcmp systemd-run --pipe --wait -p EnvironmentFile=/etc/webcmp/encryption.env \
  -p Environment=PRODUCTION=1 --working-directory=/srv/webcmp \
  /srv/webcmp/.venv/bin/python manage.py check --deploy

curl -I https://web.cmw.insmet.cu
```

> `check --deploy` tiene que salir con 0 issues. Lo único tolerado es `W008`
> (HTTPS lo termina Nginx, no Django) y se silencia en
> `config/settings/production.py`.

### Comandos del día a día

```bash
sudo systemctl restart webcmp            # reinicio sin cortar conexiones
sudo systemctl reload webcmp             # recarga de workers (SIGHUP)
sudo systemctl status webcmp
sudo journalctl -u webcmp --since "1 hour ago" -p err
```

### Rotar claves

```bash
sudo -u webcmp .venv/bin/python scripts/generate_env.py --production --rotate-keys
sudo systemctl restart webcmp
```

**Invalida todas las sesiones y cookies firmadas.** Es lo esperado al rotar.

### Migrar desde supervisor

1. `sudo systemctl stop supervisor` (o quita los dos programas de
   `/etc/supervisor/conf.d/webcmp.conf` y `supervisorctl update`).
2. Seguí los pasos 3 a 6 de arriba en el servidor nuevo.
3. Nginx debe apuntar al socket nuevo: `unix:/run/webcmp/gunicorn.sock`.
4. `nginx -t && sudo systemctl reload nginx`.
5. `gunicorn.sh` se retiró del repositorio: el unit hace su trabajo con
   `ExecStart` directo. Si el servidor viejo todavía lo tiene, no lo borres
   hasta que el nuevo esté sirviendo.

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
