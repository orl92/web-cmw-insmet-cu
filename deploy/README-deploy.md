# Despliegue automatizado

Como pasar de `sudo systemctl restart webcmp` a un deploy que se dispara solo
cuando el CI de `main` esta en verde, con gates y rollback.

La logica vive en [`deploy.sh`](deploy.sh), que corre **en el servidor**. El
workflow `.github/workflows/deploy.yml` solo se conecta por SSH y lo invoca.
Una sola fuente de verdad: si el procedimiento esta en los dos lados, el dia que
uno cambie el deploy hace cosas distintas segun por donde entro.

## Que hace, y en que orden

El orden no es estetico, es la garantia:

| # | Paso | Por que en ese lugar |
| --- | --- | --- |
| 1 | `flock` | Dos pushes seguidos no pueden migrar a la vez |
| 2 | Aborta si hay cambios sin commitear | `git checkout --force` los perderia |
| 3 | `git checkout` del SHA exacto | Desplegar un SHA, no una rama: la rama se movio entre el CI y el deploy |
| 4 | `pip install -r requirements/prod.txt` | Antes de los gates, que importan las deps |
| 5 | Gate: `makemigrations --check --dry-run` | El modelo cambio y nadie escribio la migracion. Sin esto, el error sale en el primer request de un usuario |
| 6 | Gate: `check --deploy` con la config real | Ver la nota de abajo |
| 7 | `migrate` | Antes de que el codigo nuevo atienda un request |
| 8 | `collectstatic` | Antes de que el codigo nuevo emita HTML que los referencia |
| 9 | `systemctl restart` de ambos units | `reload` NO alcanza, ver la nota de abajo |
| 10 | Health check contra Nginx local | Atraviesa Nginx, TLS y el socket: el camino completo |

### Por que el `check --deploy` del servidor y no solo el del CI

El job `deploy-check` del CI corre el mismo check, pero con valores de mentira:
base de datos que no existe, sin SMTP, `SECRET_KEY` de un par Fernet descartable.
Verifica que **el codigo** no tenga problemas de seguridad.

El gate del servidor corre contra el `.env` de verdad. Es la primera vez que se
comprueba que la `SECRET_KEY` se descifra con la `ENCRYPTION_KEY` de
`/etc/webcmp/encryption.env`, que `DB_*` apunta al PostgreSQL real y que
`EMAIL_BACKEND` no es el de consola (que `production.py` rechaza). Tarda segundos
y evita un sitio caido.

### Por que `restart` y no `reload`

`systemctl reload` (SIGHUP) recarga la configuracion de Gunicorn y los workers se
re-forkean **desde el master**, que tiene el codigo viejo en memoria. Los workers
nuevos tambien tendrian el codigo viejo. El sitio serviria los templates viejos
con los estaticos nuevos: el peor estado posible, uno que no se ve como falla.

### Por que `systemd-run` y no `manage.py` pelado

Los comandos de Django corren en una unidad transitoria con el mismo
`EnvironmentFile` y `PRODUCTION=1` que `webcmp.service`. Un `manage.py` corrido a
mano en una shell sin `PRODUCTION` cae en el perfil de **desarrollo**
(`config/settings/__init__.py` elige perfil por la variable de entorno): migra
contra sqlite3 y dice que todo bien mientras el sitio sigue en PostgreSQL.

## Rollback

Automatico: si algo falla **despues** de `migrate`, el script vuelve al commit
anterior, reinstala dependencias, recoloca estaticos y reinicia los units.

Lo que **no** hace, y hay que saber antes de confiar en el:

- **No revierte la base de datos.** Django no genera migraciones inversas y una
  operacion destructiva (`DROP COLUMN`, `AddField` con `default` + `NOT NULL`) no
  tiene hacia atras. El script avisa por pantalla cuando ya migro; si el fallo
  fue post-migracion, la base quedo con el esquema nuevo y hay que revisarla a
  mano antes de volver a exponer el sitio.
- **No toca `media/`.** Los archivos que subio la gente no se deshacen.

Manual:

```bash
sudo /usr/local/sbin/webcmp-deploy <commit-anterior>
```

## Instalacion en el servidor (una vez)

El despliegue por workflow **no** es autocontenido: la primera vez hay que
instalar el usuario, el script, la config y el sudoers a mano. Despues de eso, el
deploy es automatico.

```bash
# 1. Usuario de despliegue. Distinto de webcmp, que tiene shell /bin/false a
#    proposito: existe para correr Gunicorn, no para que alguien se loguee.
sudo useradd -m -s /bin/bash deploy

# 2. Script FUERA del checkout.
sudo install -o root -g root -m 0755 deploy/deploy.sh /usr/local/sbin/webcmp-deploy

# 3. Config.
sudo install -o root -g root -m 0600 deploy/deploy.env.example /etc/webcmp/deploy.env
sudo nano /etc/webcmp/deploy.env   # rutas y PUBLIC_HOSTNAME

# 4. Sudoers acotado a UN comando.
sudo install -o root -g root -m 0440 deploy/sudoers/webcmp-deploy /etc/sudoers.d/webcmp-deploy
sudo visudo -c
```

Por que el script va en `/usr/local/sbin` y no en `/srv/webcmp/deploy/deploy.sh`:
el script corre como root y el checkout es escribible por `webcmp`. Con el sudoers
de arriba, tener el script dentro del checkout seria una escalada de privilegios
trivial: alcanza con editar el archivo para ejecutar root.

> Si el servidor ya venia de supervisor + `gunicorn.sh`, primero
> `sudo systemctl stop supervisor` y segui los pasos 3 a 6 del README. Nginx tiene
> que apuntar a `unix:/run/webcmp/gunicorn.sock`, no a `/tmp/gunicorn-webcmp.sock`.

## Secrets de GitHub

En **Settings > Environments > production** (no en el repo: asi el environment
puede pedir aprobacion humana y las credenciales de produccion no se ven desde
cualquier workflow):

| Secret | Que es |
| --- | --- |
| `DEPLOY_HOST` | IP o hostname del servidor |
| `DEPLOY_USER` | `deploy` |
| `DEPLOY_SSH_KEY` | Clave privada ed25519, en formato PEM con el `BEGIN`/`END` |
| `DEPLOY_SSH_KNOWN_HOSTS` | Salida de `ssh-keyscan -p 22 <host>` |

`DEPLOY_SSH_KNOWN_HOSTS` no es opcional ni decorativo: el workflow usa
`StrictHostKeyChecking=yes`, asi que sin ese secret el deploy falla. Va ahi, y no
con `accept-new`, porque `accept-new` acepta cualquier clave la primera vez: un
deploy que no verifica a quien se conecta le entrega la clave de despliegue a
cualquiera que responda ese puerto.

Generar el par:

```bash
ssh-keygen -t ed25519 -C "github-actions-deploy@webcmp" -f ~/.ssh/webcmp_deploy
ssh-keyscan -p 22 <host-del-servidor> > ~/.ssh/known_hosts_webcmp
cat ~/.ssh/webcmp_deploy.pub      # -> DEPLOY_SSH_KEY (la PRIVADA es la .pub de la otra)
cat ~/.ssh/known_hosts_webcmp     # -> DEPLOY_SSH_KNOWN_HOSTS
```

## Correr un deploy a mano

Sin PR, sin CI. Para un fix caliente o un reintento:

```bash
sudo /usr/local/sbin/webcmp-deploy <sha-o-rama>
```

Desde GitHub, el boton **Run workflow** hace lo mismo y deja registro en Actions.

## Lo que el workflow NO puede hacer

Un runner hospedado de GitHub Actions hace `ssh` por el puerto 22. Si el servidor
esta atras de un firewall que solo deja entrar por VPN o por un bastion, el deploy
automatico no llega. Opciones, de peor a mejor:

1. Correr el deploy a mano (el script esta ahi para eso).
2. Self-hosted runner en la red interna.
3. Abrir el 22 restringido a las IP de GitHub.

Este caso es relevante: el host es un `.cu` de red interna. **Probalo antes de
confiar en el** con un deploy de prueba.

## Primer deploy: checklist

Antes de fiar el primer deploy automatico, probalo a mano contra un SHA
equivocado a proposito. El rollback automatico no se conoce hasta que se lo vio
funcionar una vez.

```bash
# 1. El servidor tiene /etc/webcmp/deploy.env y /etc/webcmp/encryption.env.
sudo install -o root -g root -m 0600 deploy/deploy.env.example /etc/webcmp/deploy.env

# 2. El script anda con los permisos correctos.
sudo -u webcmp /srv/webcmp/.venv/bin/python -c 'import django'   # el venv esta sano

# 3. El gate real pasa.
sudo -u webcmp systemd-run --quiet --pipe --wait \
  -p EnvironmentFile=/etc/webcmp/encryption.env \
  -p Environment=PRODUCTION=1 --uid=webcmp --gid=webcmp \
  --working-directory=/srv/webcmp \
  /srv/webcmp/.venv/bin/python manage.py check --deploy --fail-level WARNING

# 4. Deploy de verdad, a mano, con un SHA que ya sepas que es bueno.
sudo /usr/local/sbin/webcmp-deploy main

# 5. Recien ahi, probalo mal a proposito: desplegar un commit anterior y
#    confirmar que el sitio vuelve atras sin intervention.
sudo /usr/local/sbin/webcmp-deploy <commit-anterior>
```

Si el paso 3 falla, el problema es el `.env` o `encryption.env`, no el deploy.
