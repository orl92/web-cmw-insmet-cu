# Centro Meteorológico Provincial Camagüey

Sistema web del **Centro Meteorológico Provincial Camagüey** (CMP): portal público
meteorológico, panel administrativo y API REST para terceros.

**Producción:** [https://web.cmw.insmet.cu](https://web.cmw.insmet.cu)

Django 5.2 + Django REST Framework sobre PostgreSQL, interfaz con
[Tabler](https://tabler.io/), servidor Gunicorn detrás de Nginx y un worker de Huey
para correos y PDFs. Interfaz y configuración en español (`es-mx`, `America/Havana`).

---

## Índice

- [Arranque rápido](#arranque-rápido) — entorno de desarrollo en 3 pasos
- [Cómo funciona la configuración](#cómo-funciona-la-configuración) — perfiles, claves y por qué falla cerrado
- [Organización del proyecto](#organización-del-proyecto) — qué hace cada app
- [Convenciones que te van a morder](#convenciones-que-te-van-a-morder) — las reglas duras del proyecto
- [Tests](#tests) — cómo correrlos y qué corre CI
- [Probar el worker y los correos](#probar-el-worker-y-los-correos) — PDF + email de punta a punta
- [Despliegue en producción](#despliegue-en-producción) — servidor nuevo, paso a paso
- [Contribuir](#contribuir) — flujo de trabajo del proyecto
- [Licencia](#licencia)

---

## Arranque rápido

Requiere **Python 3.14** (el CI la fija y ruff apunta a `py314`).

```bash
git clone https://github.com/orl92/web-cmw-insmet-cu.git
cd web-cmw-insmet-cu

# Dependencias del sistema para PDFs (wkhtmltopdf) y MySQL (libmysqlclient)
sudo apt install libcairo2-dev pkg-config python3-dev wkhtmltopdf

# En Python 3.14 no hay ruedas para varios pins de requirements/prod.txt
# (pycairo entre otros) y hay que compilar. Sin esto pip falla con
# "Running cc --version gave [Errno 2] No such file or directory: 'cc'".
sudo apt install build-essential

# WeasyPrint (facturacion en PDF) carga libpango por cffi. Sin esto,
# `manage.py check` muere con "ffi.dlopen('libpango-1.0.so.0')".
# Ojo con el nombre: en Ubuntu 24.04+ es libpango1.0-dev, NO libpango-1.0-dev.
sudo apt install libpango1.0-dev

make setup
```

`make setup` crea el venv, instala las dependencias de desarrollo y tests, genera el
`.env` con un par de claves usable y activa los hooks de git. Faltan dos pasos:

```bash
python manage.py makemigrations      # las migraciones NO se versionan
python manage.py migrate
python manage.py add_stations_data   # Stations, Towns, Provinces
python manage.py createsuperuser
python manage.py runserver
```

En `http://127.0.0.1:8000/`. El perfil de desarrollo usa SQLite y correo a consola:
cero configuración de infraestructura.

| Target | Qué hace |
| --- | --- |
| `make setup` | venv + dependencias + `.env` + hooks |
| `make env` | Genera el `.env` solo si falta (nunca pisa el existente) |
| `make env-force` | Regenera el `.env` conservando el par de claves |
| `make test` | Suite completa |
| `make lint` | `ruff check` + `ruff format --check` |
| `make djlint` | Lint de templates |
| `make audit` | `pip-audit` sobre las dependencias de runtime |
| `make check` | `manage.py check` |

El worker de Huey corre aparte, en otra terminal:

```bash
./run_huey.sh
```

Para probar el flujo de facturas y correos de punta a punta (con sus
dependencias y su preflight), ver [Probar el worker y los correos](#probar-el-worker-y-los-correos).

<details>
<summary>Instalación manual (si no usas <code>make</code>)</summary>

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements/dev.txt
python scripts/generate_env.py --development
git config core.hooksPath .githooks
```

</details>

### Dependencias: un archivo por entorno

Cada archivo es autocontenido (incluye `base.txt` con `-r base.txt`).

| Archivo | Instala |
| --- | --- |
| `requirements/base.txt` | Runtime de la app. Sin gunicorn ni herramientas de desarrollo. |
| `requirements/dev.txt` | `base.txt` + ruff, bandit, pip-audit, djlint, pre-commit, django-debug-toolbar |
| `requirements/test.txt` | `base.txt` + django-debug-toolbar |
| `requirements/prod.txt` | `base.txt` + gunicorn y el driver de PostgreSQL |

```bash
pip install -r requirements/dev.txt   # desarrollo
pip install -r requirements/test.txt  # solo correr tests
pip install -r requirements/prod.txt  # producción
```

---

## Cómo funciona la configuración

`config/settings/` es un **paquete con perfiles**, no un monolito. El dispatcher
(`config/settings/__init__.py`) elige el perfil antes de importar nada:

| Condición | Perfil | Para qué |
| --- | --- | --- |
| `PRODUCTION` en el entorno | `production` | Servidor |
| `DEBUG=True` | `dev` | Desarrollo con `.env` |
| sin `.env` | `testing` | Suite de tests |

`PRODUCTION` gana sobre `DEBUG`. Los tres perfiles importan `base.py`, así que
comparten la misma configuración y se comportan igual salvo donde declaran una
diferencia.

### Las claves se generan fuera de Django

El bootstrap de un proyecto Django tiene una trampa: `manage.py` importa los
settings **antes** de despachar el comando, así que un comando que genera la clave
necesita que los settings ya tolerate no tenerla. Por eso el generador es un script
plano, que corre exactamente en el estado donde la aplicación todavía no puede
arrancar:

```bash
python scripts/generate_env.py --development   # SQLite, correo a consola
python scripts/generate_env.py --production    # PostgreSQL, SMTP, fail-closed
python scripts/generate_env.py --production --rotate-keys   # invalida sesiones
```

Y por eso los settings pueden **fallar cerrado**: `base.load_secret_key()` levanta
`ImproperlyConfigured` en cualquier perfil si no hay material descifrable. No hay
fallback a una clave aleatoria ni aviso silencioso — un perfil de producción sin
clave correcta no se distingue del que la tiene, y esa es exactamente la
diferencia que no querés.

El perfil `testing` es la excepción, y es deliberada: inyecta un par determinista
antes de importar `base`, que es lo que permite correr la suite en un clon limpio
sin `.env`.

### La `ENCRYPTION_KEY` no va en el `.env`

El `.env` guarda la `SECRET_KEY` **cifrada con** `ENCRYPTION_KEY`. Si las dos están
en el mismo archivo, un `.env` filtrado entrega el secreto ya descifrado: la clave
con la que se cifró viaja junto al texto cifrado.

En producción el script escribe la clave de descifrado aparte, en
`/etc/webcmp/encryption.env` (`600`, root), y systemd la carga con
`EnvironmentFile=-`. Un `.env` filtrado no entrega nada por sí solo.

---

## Organización del proyecto

Las apps viven en `apps/` y se importan como `from apps.<app>.models import ...`.

| App | Responsabilidad |
| --- | --- |
| `apps/home` | Páginas públicas: tiempo, modelos, satélites, servicios, institución |
| `apps/dashboard` | Vista agregada del panel |
| `apps/meteo` | Pronósticos, avisos, reportes meteorológicos, geografía y estaciones |
| `apps/commercial` | Clientes, servicios, suscripciones, facturación, contratos, certificados |
| `apps/publications` | Publicaciones científicas y autores |
| `apps/user_auth` | Perfil, login, usuarios, grupos, LDAP opcional |
| `apps/api` | API REST: estaciones, observaciones, pronósticos. Docs en `/api/doc/` |
| `apps/core` | Mixins, error views, configuración del sitio, envío de correo, utilidades |

`config/` tiene los settings, urls raíz y WSGI/ASGI. `templates/` contiene los
layouts base y los includes; cada app tiene sus páginas en
`apps/<app>/templates/pages/`. `static/` en desarrollo, `staticfiles/` en producción
vía WhiteNoise.

Las convenciones detalladas —modelos de dominio, permisos, estructura de URLs,
Huey— están en [`AGENTS.md`](AGENTS.md), que es la referencia técnica del proyecto.

---

## Convenciones que te van a morder

Estas reglas no son estilo: rompen cosas si no las seguís.

**No hay Node.js.** Ni bundlers, ni paso de build, ni `package.json`. Todo el
frontend es Django Templates + Tabler + JavaScript vanilla ya vendoreado. Por
legado, Tabler (CSS y JS) está en `static/dist/css/` y `static/dist/js/`; el resto
de librerías en `static/dist/libs/`. Un PR que agregue npm no se merges.

**Las migraciones no se versionan** (`.gitignore` las excluye). Cada quien corre
`makemigrations` en su máquina. Si tu cambio altera el schema, el proyecto tiene que
saberlo por el diff de modelos, no por un archivo de migración.

**Los permisos no son los de Django.** Los modelos de negocio usan
`default_permissions = ()` y definen cuatro permisos custom (`view_*`, `add_*`,
`change_*`, `delete_*`) en español. No asumas que existen por defecto.

**Los modelos con archivos usan `FileHandlerMixin`.** No lo quites: es lo que evita
perder archivos al reubicar en `media/`.

**Soft delete en modelos de negocio con datos sensibles** (Customer, Service,
ServiceSubscription, Invoice, Contract, Certificate, Warning). Se consulta por el
manager por defecto, que ya filtra `record_active=True`.

**URLs por `uuid`, no por `pk`,** en los modelos expuestos.

**Los templates usan indentación de 2 espacios** y djlint los formatea
(`make djlint`). Los templates de correo en `*/emails/` están excluidos porque son
whitespace-sensitive.

**El worker de Huey no es decorativo.** Los correos y los PDFs se generan ahí, así
que corre como un servicio aparte (`deploy/systemd/webcmp-huey.service`), no dentro
del proceso web.

---

## Tests

```bash
python manage.py test                    # suite completa
python manage.py test apps.meteo         # una app
python manage.py test apps.meteo.tests.test_forecasts
```

El CI no corre la suite completa en cada PR: detecta qué apps cambiaron y corre
solo esas. Los cambios en `config/`, `templates/`, `static/`, `requirements/` o los
workflows fuerzan la suite completa, igual que un push a `main`.

Antes de abrir un PR:

```bash
python manage.py check && python manage.py test
```

Los hooks de pre-commit (`ruff`, `djlint`, `detect-secrets`) corren solos en cada
commit. Viajan versionados en `.githooks/pre-commit` y `make setup` los activa con
`core.hooksPath`. Para correrlos sobre todo el repo:

```bash
.venv/bin/pre-commit run --all-files
```

> `pre-commit install` y `core.hooksPath` son mutuamente excluyentes: `core.hooksPath`
> hace que git ignore `.git/hooks` por completo, así que correr ambos te deja
> depurando un hook que git nunca invoca. `make setup` usa
> `pre-commit install --install-hooks` **solo** para poblar los entornos de los hooks;
> la activación la hace `core.hooksPath`.

---

## Probar el worker y los correos

El flujo de factura (PDF + correo) tiene tres dependencias que fallan en
silencio: el binario `wkhtmltopdf`, el worker corriendo, y el backend de correo.
Sin esto, el síntoma es siempre el mismo y engañoso: Huey reintenta tres veces y
la factura queda con `email_sent=True` sin que haya salido nada de tu máquina.

Este comando te dice **cuál** falta, antes de encolar nada:

```bash
# Chequeo previo: crea datos de prueba solo si todo lo demás está en su sitio
python manage.py send_test_invoice --demo

# Encolar para el worker (que corre aparte: ./run_huey.sh)
python manage.py send_test_invoice --demo

# Ejecutar en este proceso, sin levantar el worker
python manage.py send_test_invoice --demo --now

# Una factura que ya existe
python manage.py send_test_invoice <uuid>
```

> `wkhtmltopdf` no se instala con `pip`: es una dependencia del sistema. En
> Debian/Ubuntu, `sudo apt install wkhtmltopdf`. `pdfkit` es solo un wrapper; sin
> el binario, la tarea muere *antes* de enviar el correo.

### Ver el correo, no un "enviado" falso

El backend por defecto en desarrollo es `console`: imprime el mensaje y devuelve
éxito igual, así que `email_sent=True` no significa que el correo haya salido. Para
verlo de verdad, poné en tu `.env`:

```dotenv
EMAIL_BACKEND=django.core.mail.backends.filebased.EmailBackend
```

Cada correo queda como archivo en `tmp/emails/` (ignorado por git, porque lleva
datos de clientes). Para cambiar la ruta: `EMAIL_FILE_PATH=...`.

Con SMTP real usá las variables de producción y el `EMAIL_BACKEND` de Django que
corresponda. `dev` acepta cualquiera; `production` rechaza `console`, `filebased` y
`locmem` (los tres aceptan el mensaje y lo descartan) y te pide regenerar el `.env`
con `python scripts/generate_env.py --production`.

---

## Despliegue en producción

Para un servidor **nuevo**, en Ubuntu 26.04 LTS con Python 3.14 nativo. Si venís de
supervisor, hay una nota al final de la sección.

```
Nginx (TLS, estáticos, media) → Gunicorn (systemd) → PostgreSQL
                                              └──→ worker Huey (systemd)
```

Redis es opcional: el caché por defecto corre en memoria del proceso.

> Ojo: `scripts/generate_env.py --production` escribe `USE_REDIS_CACHE=True`, así que
> o instalás Redis (`sudo apt install redis-server && sudo systemctl enable --now
> redis-server`) o ponés `USE_REDIS_CACHE=False` en el `.env`. Con `True` y sin
> servidor Redis, el fallo aparece en la primera escritura al caché, en producción.
>
> Y aunque no uses Redis, el caché en memoria es **por proceso**: con varios workers
> cada uno tiene su copia y no se invalidan entre sí. Para el portal público no es
> grave; para el panel de administración, donde un estado obsoleto se traduce en
> "no veo el cliente que acabo de crear", conviene Redis.

Los tres archivos de configuración están versionados en `deploy/`. Son **ejemplos
deterministas sin secretos**: lo que cambia por instalación son rutas y certificados,
y eso se edita en el servidor.

### 1. Sistema

```bash
sudo apt update
sudo apt install -y python3.14 python3.14-venv postgresql nginx

# Usuario dedicado. El servicio NUNCA corre como root.
sudo useradd -r -s /bin/false webcmp
sudo mkdir -p /srv/webcmp && sudo chown webcmp:webcmp /srv/webcmp
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

`psycopg[binary]` ya está en `requirements/prod.txt`.

### 3. Código y `.env`

```bash
sudo -u webcmp git clone https://github.com/orl92/web-cmw-insmet-cu.git /srv/webcmp
cd /srv/webcmp
sudo -u webcmp python3.14 -m venv .venv
sudo -u webcmp .venv/bin/pip install -r requirements/prod.txt

# `generate_env.py` tiene que correr como root: escribe /etc/webcmp/encryption.env,
# que es root con modo 600 y webcmp no puede crear. Correlo como webcmp falla y no
# escribe nada (falla cerrado, lo cual esta bien).
sudo install -d -m 0755 -o root -g root /etc/webcmp
sudo .venv/bin/python scripts/generate_env.py --production

# Las migraciones NO se versionan (ver .gitignore), asi que en un clone limpio no
# existen: `migrate` solo no alcanza, hay que generarlas antes desde los modelos.
sudo -u webcmp .venv/bin/python manage.py makemigrations
sudo -u webcmp .venv/bin/python manage.py migrate
sudo -u webcmp .venv/bin/python manage.py collectstatic --no-input
```

> `manage.py` a secas, fuera del unit, no ve la `ENCRYPTION_KEY` de
> `/etc/webcmp/encryption.env` (600, root). En el perfil de producción eso hace
> que `SECRET_KEY` no se pueda descifrar. Para correrlos a mano con el mismo
> contexto que el servicio: `systemd-run --pipe --wait --uid=webcmp
> -p EnvironmentFile=/etc/webcmp/encryption.env -p Environment=PRODUCTION=1
> --working-directory=/srv/webcmp .venv/bin/python manage.py ...`, que es lo que
> hace `deploy/deploy.sh`.

El script escribe dos archivos:

| Archivo | Contiene | Permisos |
| --- | --- | --- |
| `/srv/webcmp/.env` | `SECRET_KEY` cifrada, `DEBUG=False`, `DB_*`, SMTP | `600`, **webcmp** |
| `/etc/webcmp/encryption.env` | `ENCRYPTION_KEY` (clave de descifrado) | `600`, root |

El `.env` es de `webcmp` y no de root porque Django corre como ese usuario y tiene
que poder leerlo. La `ENCRYPTION_KEY` queda en root y el `.env` en 600: entrar al
grupo `webcmp` (lo necesita Nginx, ver el paso 5) no da acceso a ninguna de las dos.

Después de generar el `.env` hay que **cambiar el hostname**: el generador escribe
`EXTERNAL_HOSTNAME=cmw.insmet.cu` por default y no tiene flag para pasarlo, así
que hay que editar a mano `EXTERNAL_HOSTNAME`, `ALLOWED_HOSTS`,
`CSRF_TRUSTED_ORIGINS` y `CORS_ALLOWED_ORIGINS`. Si no, el sitio responde
`DisallowedHost` a cada petición.

```bash
sudo nano /srv/webcmp/.env
sudo chown webcmp:webcmp /srv/webcmp/.env && sudo chmod 600 /srv/webcmp/.env
sudo chown root:root /etc/webcmp/encryption.env && sudo chmod 600 /etc/webcmp/encryption.env

# `staticfiles/` y `media/` los necesita escribibles por el usuario del servicio,
# y `.cache/` para MPLCONFIGDIR: con `ProtectSystem=full` el worker no puede
# crearse solo ese directorio, y el unit lo declara en `ReadWritePaths=`.
sudo mkdir -p /srv/webcmp/{media,logs,staticfiles,.cache/matplotlib}
sudo chown -R webcmp:webcmp /srv/webcmp/{media,logs,staticfiles,.cache}
```

### 4. systemd

```bash
sudo cp deploy/systemd/webcmp.service deploy/systemd/webcmp-huey.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now webcmp webcmp-huey
sudo journalctl -u webcmp -f
```

Los logs van a journald, no a archivos.

> **Las rutas de `/srv/webcmp` están escritas en el `.service`.** En un unit,
> `APP_DIR=/srv/webcmp` no es una clave válida de systemd y systemd tampoco expande
> variables en `WorkingDirectory=` o `ReadWritePaths=`. Si el checkout cambia de
> lugar, se editan las rutas y se verifica:
> `systemd-analyze verify /etc/systemd/system/webcmp.service`.

> **`EnvironmentFile=-` lleva el guion a propósito.** Sin la clave de descifrado, el
> servicio arranca y falla con el error accionable de `load_secret_key()`. Sin el
> guion, fallaría systemd con un error que no dice qué hacer.

### 5. Nginx

```bash
sudo cp deploy/nginx/webcmp.conf.example /etc/nginx/sites-available/webcmp.conf
sudo nano /etc/nginx/sites-available/webcmp.conf   # certificados y rutas
sudo rm -f /etc/nginx/sites-enabled/default
sudo ln -s /etc/nginx/sites-available/webcmp.conf /etc/nginx/sites-enabled/

# www-data tiene que poder tocar el socket de Gunicorn, que sale
# 0770 webcmp:webcmp. Sin esto Nginx devuelve 502 en cada respuesta y el log dice
# "connect() failed (13: Permission denied)", que no parece un problema de grupo.
sudo usermod -aG webcmp www-data

sudo nginx -t && sudo systemctl reload nginx
```

> **Reinicio de Nginx, no `reload`.** Los grupos suplementarios se leen al crear
> los workers. Un `reload` alcanza para leer la config, pero si acabás de cambiar
> la pertenencia a un grupo, reiniciá el servicio.

> **No quites `proxy_set_header X-Forwarded-Proto $scheme;`.** Django lo lee con
> `SECURE_PROXY_SSL_HEADER` para resolver `request.is_secure()`. Sin esa línea las
> cookies de sesión seguras no se envían y el usuario entra en un bucle de logout.

> **`Host` está repetido dentro de `location /`, y no es una redundancia.** En
> Nginx, `proxy_set_header` se hereda del `server` solo si el `location` no declara
> ninguno. `location /` declara dos (para el websocket), así que los del `server`
> se descartan ahí y el `Host` vuelve al default, que es `$proxy_host`: el nombre
> del upstream. Gunicorn recibía `Host: webcmp` y contestaba `DisallowedHost` en
> todas las peticiones. Si sacás esas líneas, el sitio entero responde 400.

### 6. Verificar

```bash
sudo -u webcmp systemd-run --pipe --wait \
  -p EnvironmentFile=/etc/webcmp/encryption.env \
  -p Environment=PRODUCTION=1 --working-directory=/srv/webcmp \
  /srv/webcmp/.venv/bin/python manage.py check --deploy

curl -I https://web.cmw.insmet.cu
```

`check --deploy` tiene que salir con 0 issues. Lo único tolerado es `W008` (el TLS lo
termina Nginx, no Django) y está silenciado en `config/settings/production.py`.

### Operación

```bash
sudo systemctl restart webcmp   # reinicio sin cortar conexiones
sudo systemctl reload webcmp    # recarga de workers (SIGHUP)
sudo journalctl -u webcmp --since "1 hour ago" -p err
```

Rotar claves (invalida sesiones y cookies firmadas):

```bash
sudo -u webcmp .venv/bin/python scripts/generate_env.py --production --rotate-keys
sudo systemctl restart webcmp
```

Limpiar archivos huérfanos de `media/` (tiene `--dry-run`):

```bash
sudo -u webcmp .venv/bin/python manage.py cleanup_orphan_media --dry-run
```

<details>
<summary>Si venís de supervisor + gunicorn.sh</summary>

1. `sudo systemctl stop supervisor` (o sacá los programas de
   `/etc/supervisor/conf.d/webcmp.conf` y `supervisorctl update`).
2. Seguí los pasos 3 a 6 en el servidor nuevo.
3. Nginx debe apuntar al socket nuevo: `unix:/run/webcmp/gunicorn.sock`.
4. `gunicorn.sh` ya no está en el repo; el unit lo reemplaza con `ExecStart` directo.

</details>

---

## Contribuir

El proyecto usa un ciclo de trabajo con registro: los cambios con impacto se
describen en `openspec/changes/<nombre>/` (proposal, spec, tasks) antes de
implementarse, y `AGENTS.md` describe las convenciones que hay que respetar. Es el
mismo flujo que usa la documentación interna; no es burocracia de comité, es lo que
permite retomar un trabajo a medias.

Flujo práctico:

1. `git checkout -b feat/lo-que-sea`
2. Commits conventional: `feat(meteo): agregar pronóstico de 5 días`. Un commit es
   una unidad de trabajo revisable, con sus tests y su documentación adentro.
3. `python manage.py test` en verde antes de pushear.
4. PR contra `main`. El CI corre los tests de las apps que tocaste.

Autores: el Instituto de Meteorología de Cuba.

## Licencia

MIT. Ver [LICENSE](LICENSE).

Centro Meteorológico Provincial Camagüey — Instituto de Meteorología de Cuba.
