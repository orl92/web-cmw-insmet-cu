# 024-deploy-check-fail-closed

## Por qué

El spec promovido `013-check-deploy-ci` describe el gate de despliegue tal como
funcionaba antes del trabajo de producción, y hoy **contradice al código**:

- Exige que `base.py` conserve un fallback a `get_random_secret_key()` cuando no
  hay par descifrable, "porque fallar cerrado dejaría sin arranque al comando
  `generate_env`". Ese comando ya no existe y el fallback tampoco: `base.py`
  levanta `ImproperlyConfigured` en los cuatro casos sin clave.
- Menciona `EphemeralSecretKeyWarning` tres veces. Ese símbolo no existe en el
  repositorio.
- Nombra `python manage.py generate_env` como el fix en dos requisitos. El
  generador real es `scripts/generate_env.py`, un script que no importa Django.

Un spec que exige lo contrario de lo que el código hace no es documentación
desactualizada: es un contrato que invites a reintroducir el bug. Alguien que lo
lea-va a "arreglar" el fail-closed poniendo el fallback de vuelta, y con él
vuelve el síntoma que motivó el cambio: sesiones que se invalidan en cada
reinicio sin que nada falle.

## Qué cambia

Se sincroniza `013-check-deploy-ci` con la realidad, y de paso se fija la
decisión de diseño que evita la regresión:

1. Se elimina el requirement del fallback efímero.
2. Se agrega el requirement del fail-closed en todos los perfiles, con la
   excepción documentada del perfil `testing`.
3. Se agrega el requirement que ubica al generador **fuera de Django**, que es lo
   que hace posible el punto 2.
4. Se agrega el requirement de que la clave de descifrado no viva junto al
   texto cifrado.
5. Se corrigen las dos menciones al comando eliminado.

Lo que **no** cambia: el gate sigue siendo `check --deploy --fail-level WARNING`
con `PRODUCTION` en el entorno, `W008` sigue silenciado por Nginx, `X_FRAME_OPTIONS`
sigue en `DENY`, y los jobs existentes siguen intactos. Ese trabajo ya era correcto
y no se toca.

## Fuera de alcance

Los units de systemd, el ejemplo de Nginx y la separación de `encryption.env` no
tienen spec propio. Se documentan en `README.md` (procedimiento) y en
`AGENTS.md` (convenciones). Crear una capability nueva para el deploy es una
decisión de proyecto, no una reparación de un spec roto: queda planteada aparte.

## Criterios de aceptación

- `013-check-deploy-ci` ya no nombra `manage.py generate_env` ni
  `EphemeralSecretKeyWarning` en ningún requirement.
- El requirement del fail-closed cubre dev, production y la excepción de testing.
- El requirement del generador externo dice por qué un management command no
  serviría, para que la decisión no se revierta por "simplificación".
