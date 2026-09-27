# Split de requirements y bootstrap de hooks

## Objetivo

Un archivo de dependencias por entorno, con un solo comando de onboarding para un dev nuevo.

## Problema

`requirements.txt` se declaraba runtime pero incluía `gunicorn` (el binario del servidor), y
`requirements-dev.txt` era solo-lint. Cada job de CI terminaba instalando dos archivos porque
ninguno cubría su entorno. Además no había `Makefile` ni hook versionado, así que clonar el repo
no daba ninguna ruta de onboarding.

## Alcance

- `requirements/{base,dev,test,prod}.txt` con herencia `-r base.txt`; se borran `requirements.txt`
  y `requirements-dev.txt`.
- Pin de las 89 dependencias directas a las versiones instaladas.
- `.githooks/pre-commit` versionado (0755) + `Makefile` (`setup`, `hooks`, `check`, `test`,
  `lint`, `djlint`, `audit`).
- `.github/workflows/{ci,security}.yml` y `dependabot.yml` actualizados.
- `README.md`, `AGENTS.md`, `SECURITY.md`, `openspec/config.yaml`.

## Fuera de alcance

- Migración a Django 6: change diferido. Django queda en `5.2.17`.
- Partición de `config/settings.py` por entornos: change propio, radio de explosión alto.

## Decisiones

| Decisión | Razón |
|---|---|
| `pip-audit` corre **dos veces**, contra `base.txt` y `prod.txt` | Auditar solo `base.txt` sacaba a `gunicorn` de la cobertura de CVE. El split creaba esa regresión de seguridad. |
| Dependencias transitivas **no** se pinean | `multidict` (6.9.1, hay 7.0.0) llega por `yarl`←`aiohttp`. Pinear transitivas se rompe con cada upgrade del padre. |
| `pip` no se pinea | No es dependencia del proyecto. |
| Django en `5.2.17` | La migración a 6.1.1 es un change diferido explícito. |
| `pre-commit install --install-hooks` **y** `core.hooksPath` juntos en `make setup` | No es redundancia: `hooksPath` hace que git ignore `.git/hooks` por completo. El `install` solo puebla los entornos de los hooks (que se descargan de PyPI en el primer uso); lo que activa el hook es el `git config`. Sin `--install-hooks`, un fallo de red en el primer commit deja al dev trabado. |
| Versiones que parecen typos: `flexcache==0.3`, `flexparser==0.4`, `django-csp==4.0`, `reportlab==5.0.1`, `python-dateutil==2.9.0.post0` | Son las versiones reales publicadas. `post0` es un post-release PEP 440 válido. No "corregir". |

## Verificación

- `manage.py check`: 0 issues.
- `manage.py test`: **797/797 OK**.
- `pre-commit run --all-files`: 8 hooks, exit 0.
- `pip install --dry-run` de los 4 entornos: **0 "Would install"**, rc=0.
- Contrato de dependencias: 89 directas declaradas, **0 discrepancias** contra lo instalado,
  41 transitivas resueltas por el resolver (89 + 41 + 1 pip = 131 instalados).
- Cero referencias operativas a los archivos borrados.
- `Makefile`: 17 recetas con tabs reales, 0 con espacios.

TDD: no aplica. El cambio no altera código de aplicación; los pines no cambian ninguna versión
instalada (`--dry-run` prueba 0 instalaciones), así que el comportamiento no puede variar.

## Riesgo

**`PYSEC-2026-2860` / `CVE-2025-26240`** (`pdfkit` 1.0.0, GHSA-9g3x-6x24-vf9f): `from_string`
permite ejecutar JavaScript en el contexto del servidor y exfiltrar archivos locales.
`fix_versions: []`: 1.0.0 es la única versión publicada, no hay a qué actualizar.

No lo introduce este cambio — el `base.txt` sin pinear audita idéntico. CI ya lo whitelistea en
`ci.yml:150-151` asumiendo que el HTML es generado internamente. Auditar si ese uso es explotable
es un change aparte.

## Progreso

Rama `chore/requirements-split`, 8 work-unit commits sobre `e9ad51a`, árbol limpio.

| Commit | Unidad |
|---|---|
| `42cf75d` | `refactor(deps)`: split + todas las referencias (atómico: separarlo rompe CI) |
| `37845ed` | `build`: hook versionado + `Makefile` |
| `1819b11` | `docs`: contrato de entornos y bootstrap |
| `9ac87ea` | `chore(odd)`: registro |
| `48299ee` | `chore(odd)`: criterios verificados |
| `eeeb1af` | `refactor(deps)`: pin de las 89 directas |
| `915a4e7` | `chore(odd)`: pin y tabla de work units |
| `de9e11a` | `docs(agents)`: quitar el ritual de verificación que duplicaba gentle-ai |

## Revisión nativa

**No revisada.** RDD quedó apagado a nivel de clon (`clone_local`), así que la entrega va por
política ordinaria del repo y se reporta `disabled/unmanaged`. No hay PASS ni aprobación
inventada.

La revisión 4R se intentó y quedó inconclusa: el free tier de OpenCode no sirve los subagentes
revisores (`OpenCode's free tier can only be used from within OpenCode`). La transacción
`review-f0b98ad0243be664` quedó ligada y obsoleta (congelada sobre un árbol anterior al pin), sin
capturar. No es un defecto de gentle-ai: `doctor` da 8/8, los agentes revisores heredan el modelo
por defecto y `review capabilities` no expone ningún knob de modelo o provider.

Evidencia en su lugar: 797 tests, `check` limpio, 8 hooks verdes, resolución de los 4 entornos sin
cambios y contrato de dependencias verificado. La apertura y el merge del PR son decisión del
mantenedor.
