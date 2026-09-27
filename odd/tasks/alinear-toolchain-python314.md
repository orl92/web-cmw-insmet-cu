# Alinear toolchain a Python 3.14

## Objetivo

Dejar la máquina de desarrollo, los hooks de pre-commit y CI hablando el **mismo
intérprete (3.14)** y las **mismas versiones de herramientas**, para que un commit
que pasa los hooks local no pueda ser rechazado por CI.

## Problema

La máquina de trabajo corre Python 3.14.7, pero el proyecto declaraba 3.12 en cinco
lugares (siete ocurrencias). Además, `ruff` y `djlint` vivían en **tres canales de
versión independientes** sin ningún dueño de la alineación:

| Canal | ruff | djlint | Quién lo fija |
|---|---|---|---|
| Hooks de git | `v0.16.1` | `v1.44.0` | `rev:` en `.pre-commit-config.yaml` |
| Venv local | `0.16.9` | `1.46.2` | resolución de pip |
| CI | `0.16.8` | `1.46.1` | pins de `requirements-dev.txt` |

Los pins de CI no existían en ningún entorno real; el venv ya los había superado.

**Por qué esto produce errores concretos:** el hook `djlint-reformat-django`
reescribe templates con 1.44.0 mientras CI valida con
`djlint . --reformat --check` en 1.46.1 — dos minors de diferencia. La salida del
hook puede ser exactamente lo que CI rechaza. El mismo drift existe **dentro de CI**:
el job `precommit` instala `requirements-dev.txt` y luego corre
`pre-commit run --all-files`, que ignora esos binarios y construye los hook envs
desde los `rev:`.

Causa raíz del drift recurrente: `.github/dependabot.yml` no declara el ecosistema
`pre-commit`, así que bumpea los pins cada lunes y es ciego a los `rev:`.

## Por qué 3.14 y no 3.12

- `apt` en Debian forky/sid no ofrece ninguna `python3.X` en su índice; 3.12 solo
  sería alcanzable vía `uv` o compilación desde fuente.
- La máquina de trabajo del autor es 3.14.7 y será la máquina de uso diario.
- **Compatibilidad verificada empíricamente:** `pip check` sobre el venv 3.14 responde
  `No broken requirements found`, con las 8 dependencias de extensión nativa del
  proyecto ya resueltas con ruedas: `cryptography`, `cffi`, `numpy`, `scipy`, `lxml`,
  `pillow`, `contourpy`, `pycairo`. Este era el riesgo real: sin rueda para 3.14 se
  compila en local y se rompe en CI.
- Django 5.2.17 declara soporte `Programming Language :: Python :: 3.10` a `3.14`.
- `actions/setup-python` resuelve versiones desde un manifiesto dinámico, así que
  3.14 no obliga a subir el major de la action.

## Alcance

- Unificar el intérprete declarado en 3.14 (7 ocurrencias en 2 workflows).
- Unificar ruff en `0.16.9` y djlint en `1.46.2` en los tres canales.
- Declarar el ecosistema `pre-commit` en Dependabot para que el drift no se regenere.
- Instalar los hooks en esta máquina y verificarlos contra todo el repo.

## Fuera de alcance (deliberado)

- **No** se sube el major de las actions (`setup-python@v5`, `checkout@v4` → `@v7`).
  3.14 no lo requiere y sería un upgrade no solicitado.
- **No** se cambian pins de `requirements.txt` (producción). Solo `requirements-dev.txt`.
- **No** se migra el historial de OpenSpec. Tras archivar 023-landing-page no queda
  ningún change activo que invalide los docs de `openspec/changes/archive/`.

## Tareas

- [x] T1. `.pre-commit-config.yaml`: `rev` de ruff `v0.16.1` → `v0.16.9`; `rev` de
      djlint `v1.44.0` → `v1.46.2`. Route: delegated writer.
- [x] T2. `requirements-dev.txt`: restaurar los 6 pins (descartar el despineo sin
      commitear) y bumpear `ruff==0.16.9`, `djlint==1.46.2`. Route: delegated writer.
- [x] T3. `.github/dependabot.yml`: agregar ecosistema `pre-commit` para `/` con el
      mismo grupo minor/patch y timezone que los existentes. Route: delegated writer.
- [x] T4. `.github/workflows/ci.yml` (5 ocurrencias) y `.github/workflows/security.yml`
      (2 ocurrencias): `python-version: "3.12"` → `"3.14"`. Route: delegated writer.
- [x] T5. `pyproject.toml`: `target-version = "py312"` → `"py314"`. Route: delegated writer.
- [x] T6. Docs: `AGENTS.md` línea 5 y `openspec/config.yaml` línea 7 al 3.14. Además
      commitear el scrub ya presente de la línea del proxy. Route: delegated writer.

Tareas añadidas al descubrir que **main estaba rojo por 3 causas ajenas** al
alineamiento de toolchain (ver "Hallazgo transversal" abajo):

- [x] T9. `.pre-commit-config.yaml`: `exclude: '^static/'` **por hook** en el bloque
      `pre-commit-hooks`. El `exclude` a nivel de bloque es un no-op silencioso: el
      schema de pre-commit (`clientlib.py`) solo reconoce `repo`/`rev`/`hooks` y el
      filtrado real (`commands/run.py`) solo lee `hook.exclude`. `pre-commit
      validate-config` avisa con WARNING pero sale 0 — falla en silencio.
- [x] T10. `pyproject.toml`: `quote_style = "single"` en `[tool.djlint]`.
- [x] T11. `djlint . --reformat` sobre 19 archivos de templates.
- [x] T12. 3 defectos reales de djlint: 2× T045 (tag de template dentro de comentario
      HTML, que igual se ejecutaba) y 1× H043 (`<button>` sin `type`).
- [x] T13. `.github/workflows/ci.yml`: el job `test` instala `requirements-dev.txt`
      además de `requirements.txt`.
- [x] T14. `pre-commit install --install-hooks` + `pre-commit run --all-files` en exit 0.
- [x] T15. `.secrets.baseline` regenerado (solo `line_number` 73→76 de una entrada
      existente + `generated_at`; cero entradas nuevas).

## Hallazgo transversal: main estaba rojo por 3 causas

Verificado contra los logs de CI (run `36247258980`, main en `39722d2`). Sexta
corrida fallida consecutiva, desde el 2026-09-17.

| Job | Step que falla | Causa |
|---|---|---|
| `Templates (djlint)` | `djlint . --reformat --check` | 336 errores de djlint, 333 de ellos T002 |
| `Pre-commit hooks` | `pre-commit run --all-files` | `end-of-file-fixer` modificaba 14 archivos, 2 vendoreados |
| `Tests (Django)` | suite completa | `ModuleNotFoundError: No module named 'debug_toolbar'` |

**La causa raíz de T002 no era estilo, era configuración.** `djlint` usa
`quote_style` con default `"double"`, mientras el repo entero usa comillas simples.
Declarar `quote_style = "single"` baja los errores de **336 a 6** sin suprimir nada:
T002 pasó a enforcing de la convención real. Los 6 restantes eran strings y atributos
dentro de tags (`{% now "d/m/Y h:i:s A" %}`, `with class="login-image"`), que
`--reformat` normalizó. `T002` **no** quedó en la lista `ignore`.

**`tabler-marketing.min.css` lo agregó 023-landing-page** (task 2.1b de ese change),
y fue lo que tir abajo el job `pre-commit` de forma permanente: el hook modificaba el
archivo, salía con exit 1, y CI nunca commiteaba el fix. El hook no puede "arreglar"
código vendoreado — `AGENTS.md` lo prohíbe — así que la corrección es excluirlo.

**El test de debug_toolbar no estaba mal.** Su docstring dice que una regresión que
fugue el toolbar a producción debe "fail closed in CI instead of being skipped", y su
comentario dice "Required by requirements-dev". El bug estaba en el workflow: el job
`test` instalaba solo `requirements.txt`. Debilitar el test habría sido un error; se
copió el patrón que el job `security` ya usaba.

## Criterios de aceptación

- [x] Los 3 canales declaran la misma versión de ruff y de djlint.
      Verificado: hook ruff `0.16.9` = venv `0.16.9`; hook djlint `1.46.2` = venv
      `1.46.2`; hook envs en `py_env-python3.14`.
- [x] `pre-commit run --all-files` pasa en exit 0 sin modificar archivos.
- [x] `ruff check .` no reporta errores.
- [x] `djlint . --lint` reporta 0 errores y `--reformat --check` no pide cambios.
- [x] `python manage.py check` sin errores.
- [x] La suite de tests pasa: 797 tests, `OK`, 217s.
- [x] No queda ninguna referencia a `3.12` / `py312` en CI, tooling ni docs (0 resultados).

## Verificación

Resultado observado el 2026-09-27, venv en `.venv/` (Python 3.14.7):

```
ruff check .            -> PASS (exit 0)
ruff format --check .   -> PASS (exit 0)
djlint . --lint         -> PASS (0 errores)
djlint . --reformat     -> PASS (0 cambios)
manage.py check         -> PASS
manage.py test          -> PASS (797/797 OK, 217s)
pre-commit --all-files  -> PASS (exit 0)
```

## Configuración TDD

No aplica. Este cambio no altera comportamiento de aplicación: alinea declaraciones
de versión, configuración de tooling y 3 defectos de template. No se escriben tests
nuevos; la suite existente es la que debía seguir verde, y sigue verde.

## Diff resultante

8 config/docs · 8 `.py` (PEP 758) · 21 templates · 12 `.md` (newline final).

## Progreso

Todas las tareas T1-T15 completas y verificadas. **Sin commitear** — pendiente de
decisión del usuario sobre estrategia de commit (estamos en `main`).

## Pendiente de despliegue (fuera del repo)

Actualizar producción a Python 3.14. `gunicorn.sh:19` corre `${DJARDIR}/.venv/bin/
gunicorn`, o sea que producción usa el venv del repo: con el reformat PEP 758, el
servidor **requiere** 3.14 o no arranca. No se hizo ningún trabajo remoto.

## Próximo paso

Commit con estrategia a definir por el usuario, luego archivar `023-landing-page`.
