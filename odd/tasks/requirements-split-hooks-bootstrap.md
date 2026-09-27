# Requirements split + hooks bootstrap

## Objetivo

Que cada entorno se instale con **un solo archivo** y que un dev nuevo pueda deixar el
proyecto listo ejecutando **un solo comando**, sin leer `AGENTS.md` para descubrirlo.

## Problema

Hoy el contrato de entornos está roto en tres vías:

1. `requirements.txt` dice ser "runtime" (`SECURITY.md:55`), pero incluye **`gunicorn`**,
   que no es un import de la app: es el binario del servidor. Categorización falsa.
2. `requirements-dev.txt` es **solo-lint** (8 deps, ninguna de la app). Consecuencia real:
   cada job de CI que necesita la app tiene que instalar **dos** archivos, y adivinar cuáles.
   Ese fue exactamente el bug de `deploy-check` (PR #75, commit `aea9b25`).
3. Un dev nuevo tiene que saber, sin que nadie se lo diga, que corre **dos** `pip install`
   distintos según su máquina. `README.md:88` solo documenta uno de los dos.

Además no existe ninguna ayuda de onboarding: no hay `Makefile`, no hay hook versionado, y el
`README.md:54` declara "Python 3.8+" — valor obsoleto desde el reformat a Python 3.14.

## Por qué ahora

El PR #75 dejó los gates verdes, y el diagnóstico es correcto: el split no es cosmético,
convierte la suite de tests (muerta hasta hoy) en un gate real sobre un contrato de deps
que sigue siendo ambiguo. Arreglarlo ahora, con main quieto, es más barato que hacerlo
cuando haya UI en vuelo.

## Alcance

### 1. `requirements/` con herencia desde base

| Archivo | Contenido |
|---|---|
| `base.txt` | runtime de la app — los 81 actuales **menos `gunicorn`** |
| `dev.txt`  | `-r base.txt` + linters + `pip-audit` + `django-debug-toolbar` + `setuptools` + `wheel` |
| `test.txt` | `-r base.txt` + `django-debug-toolbar` |
| `prod.txt` | `-r base.txt` + `gunicorn` |

`django-debug-toolbar` va en **dev y test**: es una herramienta de desarrollo (`DEBUG=True`)
pero `apps/core/tests/test_debug_toolbar.py` **afirma que está instalada** en CI, donde
`DEBUG=False`. Duplicar una línea entre dev y test es correcto; moverla a `base` sería
meter una dependencia de desarrollo en producción.

Se **eliminan** `requirements.txt` y `requirements-dev.txt`. No se dejan shims: dos archivos
que solo dicen `-r base.txt` son ruido, y producción instala a mano (documentado en README,
sin script de deploy en el repo).

### 2. Auditoría de dependencias — arreglar una regresión antes de crearla

`pip-audit` hoy corre contra `requirements.txt`, que **incluye `gunicorn`**. Auditar solo
`base.txt` dejaría fuera al servidor WSGI, donde han salido CVES de request smuggling.
El job debe auditar `base.txt` **y** `prod.txt`.

### 3. Bootstrap de hooks

Git no tiene hook de `clone`. Lo que se puede hacer es que el hook **viaje versionado** y que
activarlo sea un comando. `git config core.hooksPath .githooks` hace que git ignore
`.git/hooks` por completo, así que `pre-commit install` y esta vía **son excluyentes** —
documentarlo, no dejar que alguien corra ambos y se confunda.

`.githooks/pre-commit` debe preferir el binario del venv del repo y caer a `PATH`, para que
funcione sin activar el venv.

`make setup` deja todo listo: venv, deps, hooks.

### 4. Documentación

`README.md` (versión de Python, installs, hooks, producción), `AGENTS.md`, `SECURITY.md:55`,
`openspec/config.yaml` (declara `requirements.txt` como "single source of truth").

## Fuera de alcance

- Partir `config/settings.py` en un paquete `base/dev/prod`. Es buena práctica documentada
  por Django, pero `DJANGO_SETTINGS_MODULE` aparece en `manage.py`, `wsgi.py`, `asgi.py`,
  `config/huey.py`, `gunicorn.sh`, `run_huey.sh`, supervisor y cada job de CI. Radio de
  explosión demasiado grande para mezclarlo con esto. Change SDD propio, después.
- `actions/checkout@v4` → `v5` (Node 20 deprecado). Fuera de alcance desde #75.
- Actualización remota de producción. Sin autorización.

## Rutas declaradas

| Tarea | Ruta | Trigger |
|---|---|---|
| T1 `requirements/` | delegated writer | 13 archivos no triviales |
| T2 workflows + dependabot | delegated writer | mismo writer, mismo cambio |
| T3 hooks bootstrap | delegated writer | mismo writer |
| T4 docs | delegated writer | mismo writer |
| Verificación | inline | `check`, `test`, `pre-commit` |
| Commits | inline | 3 work units |

## Criterios de aceptación

- [ ] `pip install -r requirements/{base,dev,test,prod}.txt` resuelve un entorno usable
- [ ] Cero referencias a `requirements.txt` / `requirements-dev.txt` fuera de specs históricos
- [ ] Cada job de CI instala **un** archivo
- [ ] `pip-audit` cubre `base.txt` **y** `prod.txt`
- [ ] `make setup` funciona desde cero
- [ ] `git config core.hooksPath .githooks` deja el hook ejecutándose sin activar venv
- [ ] `manage.py check` y `manage.py test` en verde
- [ ] `pre-commit run --all-files` en verde

## Verificación

```bash
python manage.py check
python manage.py test
pre-commit run --all-files
grep -rn "requirements\.txt\|requirements-dev\.txt" --include="*.yml" --include="*.md" --include="*.toml" --include="*.sh" . | grep -v "^\./\.venv\|^\./static"
```

## Riesgo

**Medio.** Toca los workflows que hoy están verdes. Mitigación: el cambio es puramente de
rutas de archivo; ningún paquete cambia de versión, así que el resultado de `pip install`
debe ser idéntico. Si un job falla, la causa es una referencia perdida, no una regresión de deps.

## Progreso

_(se actualiza por tarea)_
