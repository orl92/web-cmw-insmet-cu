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

- [x] `pip install -r requirements/{base,dev,test,prod}.txt` resuelve un entorno usable
      — verificado por expansión recursiva: `expand(dev) ∪ expand(prod)` == conjunto viejo,
      **89 paquetes, 0 versiones cambiadas, 0 añadidos, 0 eliminados**.
- [x] Cero referencias a `requirements.txt` / `requirements-dev.txt` fuera de specs históricos
      — el grep devolvió 60 hits en `openspec/changes/archive/**` (registros históricos, no
      editables a propósito) y 13 en `odd/tasks/` (registro del propio cambio). Con el
      patrón corregido que excluye ambos: **0 hits**.
- [x] Cada job de CI instala **un** archivo — 8 jobs verificados
- [x] `pip-audit` cubre `base.txt` **y** `prod.txt`
- [x] `make setup` funciona desde cero — `make help` se auto-documenta; `make check/lint/djlint` verdes
- [x] `git config core.hooksPath .githooks` deja el hook ejecutándose sin activar venv
      — ejecutado vía `sh .githooks/pre-commit ruff`: resuelve `.venv/bin/pre-commit`,
        stashea y restaura limpio
- [x] `manage.py check` y `manage.py test` en verde — `check` 0 issues; `test` **797/797 OK**
- [x] `pre-commit run --all-files` en verde — 8 hooks, exit 0, nada reformateado
- [x] `Makefile` usa tabs reales (17 líneas con `^I`, 0 con espacios)

## Desviaciones registradas

- `gunicorn` **no estaba pineado** (`requirements.txt:22` era `gunicorn` pelado, sin `==`).
  Se copió verbatim. Nada se pineó que antes no lo estuviera, así que el contrato de "0 cambios
  de versión" se sostiene. **Pendiente de decisión:** pinearlo en `prod.txt` sería una mejora
  de reproducibilidad, pero introduce una restricción que antes no existía.
- El writer editó dos archivos fuera de spec (`test_csp.py`, `test_debug_toolbar.py`): sus
  comentarios nombraban archivos que este cambio borra. Corrección necesaria, conservada.

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

4 work-unit commits sobre `e9ad51a` (main tras el merge de PR #75):

| Commit | Unidad |
|---|---|
| `42cf75d` | `refactor(deps)`: split + todas las referencias (atómico: separarlo rompe CI) |
| `37845ed` | `build`: `.githooks/pre-commit` + `Makefile` |
| `1819b11` | `docs`: README, AGENTS.md, SECURITY.md, openspec/config.yaml |
| `9ac87ea` | `chore(odd)`: este documento |

Rama `chore/requirements-split`. **Sin PR abierto todavía.**

## Revisión nativa (RDD) — inconclusa por entorno

- Riesgo evaluado: **high**, 18 paths, 507 líneas. Señales: `executable_mode`
  (`.githooks/pre-commit`), `hot_path` (security.yml), `shell_source` (ci.yml).
- Consentimiento del usuario: **concedido** (envelope v3 rehusado correctamente).
- Transacción congelada y ligada: lineage `review-f0b98ad0243be664`, `state: reviewing`,
  presupuesto de corrección 200 líneas, 4 lentes 4R pendientes.
- **No se pudo recolectar**: los subagentes revisores no arrancan en este contexto
  (`OpenCode's free tier can only be used from within OpenCode`). Dos intentos idénticos;
  el STATUS reofreció el mismo slot cada vez y la transacción sigue intacta.
- **No se fabricó PASS.** La revisión de este candidato está pendiente; la entrega
  sigue siendo decisión del usuario bajo política ordinaria del repo.

---

# T5 — Pinear dependencias directas a la versión instalada

> Sección agregada después de T1–T4. Checkboxes sin marcar a propósito: los marca el usuario
> tras verificar. **Sin commit.**

## Objetivo

Cerrar la desviación que T1 dejó registrada: el split preservó el conjunto de dependencias
**exacto** pero conservó los pines tal cual, así que `base.txt` terminó con 80 paquetes y
**solo 2 pineados**. Un `pip install -r requirements/base.txt` mañana resolvería versiones
distintas a las que hoy corren los 797 tests. Esto no cambia el entorno: cambia la
**reproducibilidad** del contrato.

## Alcance

Solo `requirements/{base,dev,prod}.txt`. `test.txt` ya estaba 100% pineado y queda intacto.
Fuera de alcance: workflows, dependabot, docs, hooks, `Makefile`, código Python.

## Decisiones

- **La versión instalada es la fuente de verdad.** Se leyó con `pip list --format=json` del
  propio `.venv` y se cruzó con `pip show` en 12 paquetes de versión inusual. Cero versiones
  inventadas, cero consultas a índices remotos.
- **Matching por nombre canónico (PEP 503)**, no por cadena: `PyHanko`/`pyHanko`,
  `Pint`, `rlPyCairo`, `MetPy`, `PyYAML` conservan su capitalización original en el archivo
  (el proyecto ya usaba esa forma) aunque `pip list` los devuelva en minúsculas.
- **Solo dependencias directas.** Las 41 transitivas del venv (`multidict`, `yarl`, `aiohttp`,
  `frozenlist`, `et-xmlfile`, `pyasn1`, `propcache`, …) se dejan sin pinear: fijarlas congela
  la resolución del resolver y convierte un bug de dependencia transitiva en un conflicto
  manual. `multidict` es el caso testigo — 6.9.1 instalado, 7.0.0 disponible, y llega por
  `yarl`←`aiohttp`←`pyHanko`.
- **`pip` no se pinea**: no es dependencia del proyecto, llega por `pip-api`←`pip-audit`.
- **Django se queda en `5.2.17`.** Es la versión instalada y la que corre la suite. La
  migración a Django 6.1.1 es un change posterior explícitamente diferido por el usuario;
  aquí es restricción dura, no sugerencia. El script de pineo tenía un guard que abortaba si
  `Django` salía de `5.2.17`.
- **Ni install, ni upgrade, ni resolve.** Solo edición de texto. Las tres resoluciones se
  hicieron con `pip install --dry-run`.

## Volumen

| Archivo | Pineados ahora | Ya pineados | Total deps |
|---|---|---|---|
| `base.txt` | **78** | 2 (`Django`, `redis`) | 80 |
| `dev.txt` | **2** (`setuptools`, `wheel`) | 6 | 8 |
| `prod.txt` | **1** (`gunicorn`) | 0 | 1 |

**81 paquetes pineados en total.** Formato preservado: una dep por línea, orden original
intacto, sin comentarios nuevos, sin líneas en blanco extra, sin cambios de trailing newline
(`git diff --stat` = 81 inserciones / 81 eliminaciones, una por línea tocada).

## Criterios de aceptación

- [ ] 0 líneas de dependencia sin `==` en `base.txt` / `dev.txt` / `prod.txt`
- [ ] `Django==5.2.17` intacto
- [ ] `pip install --dry-run` de `test.txt`, `dev.txt` y `prod.txt` resuelve **sin** pedir
      instalar nada (0 líneas `Would install`)
- [ ] Contrato de reproducibilidad: los 89 nombres declarados con pin coinciden exactamente
      con lo instalado — 0 discrepancias
- [ ] `pip-audit -r base.txt` y `-r prod.txt` sin CVEs **nuevas**
- [ ] `make check` verde
- [ ] TDD: **N/A** — no hay código, solo metadatos de dependencias. Sin test que escribir.

## Verificación ejecutada

```bash
grep -E '^[a-zA-Z]' requirements/base.txt requirements/dev.txt requirements/prod.txt | grep -v '=='
grep '^Django' requirements/base.txt
.venv/bin/python -m pip install --dry-run -r requirements/{test,dev,prod}.txt
.venv/bin/python -m pip list --format=json
.venv/bin/pip-audit -r requirements/{base,prod}.txt
make check
```

- **0** líneas sin pin. `grep '^Django'` → `Django==5.2.17`.
- Los tres `--dry-run` salen `rc=0` con **0** `Would install`: los 89 pines son exactamente
  lo que ya está en el venv, y las 41 transitivas las resuelve el resolver sin conflicto.
- **Conteo**: 89 directos pineados + 41 transitivas + `pip` = 131 paquetes instalados.
  Cuadra sin huecos ni sobrantes.
- `make check` → `System check identified no issues (0 silenced).`

## Desviaciones registradas

- **CVE pre-existente, no introducido por el pineo.** `pip-audit` falla (`rc=1`) en `base.txt`
  y `prod.txt` con **PYSEC-2026-2860** (alias **CVE-2025-26240**, GHSA-9g3x-6x24-vf9f) sobre
  `pdfkit 1.0.0`: *"the `from_string` method enables the execution of JavaScript code within
  the context of the server application and the exfiltration of local files"*. Sin
  `fix_versions` — **1.0.0 es la única versión publicada**, así que no hay a qué actualizar.
  Se auditó también el `base.txt` **sin pinear** desde `HEAD` (`git show HEAD:...`) y devuelve
  **exactamente la misma salida**: el CVE ya estaba, el pin solo lo hace explícito. No se
  actualizó el paquete; arreglarlo es un change aparte.
- **`pip-audit` 2.10.1 duplica la fila** del mismo `PYSEC-2026-2860` (2 filas, 1 advisory).
  Es un quirk de la herramienta, no dos vulnerabilidades distintas.

## Versiones notables (para el change de Django 6 / upgrades futuros)

Todas confirmadas con `pip show` además del `pip list`:

- `flexcache==0.3` y `flexparser==0.4` — Forestry, versiones de una sola cifra; parecen
  typos pero son las reales.
- `django-csp==4.0` — versión corta, sin micro.
- `reportlab==5.0.1`, `pandas==3.0.6`, `numpy==2.5.3` — minors grandes.
- `python-dateutil==2.9.0.post0` — sufijo post-release, PEP 440 válido.
- `certifi==2026.7.22`, `tzdata==2026.4`, `rpds-py==2026.6.3` — calver.
- `setuptools==84.0.0`, `packaging==26.3`, `wheel==0.48.0` — pins de toolchain en `dev.txt`.
- `gunicorn==26.2.0` — cierra la desviación de T1 que lo dejó pelado.

## Riesgo

**Bajo.** El cambio es puramente declarativo: ningún job de CI instala distinto porque los
89 pines coinciden con lo que ya se resolvía. El único efecto observable es que un
`pip install` en una máquina nueva envejece — que es exactamente el objetivo. El
`--dry-run` de los tres entornos lo confirma.
