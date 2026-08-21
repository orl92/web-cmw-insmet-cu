# Tasks — 093-deps-docs-alineacion

## Django y dependencias

- [ ] Auditar si el código usa features de Django 5.2 (grep por APIs nuevas/deprecadas). Decidir: subir a 5.2.x o mantener 5.1.4.
- [ ] `requirements.txt` — Fijar TODAS las deps con `==` (usar versiones instaladas en `.venv` como base).
- [ ] Eliminar dependencias sin uso (`dotenv`, `str2bool` — verificar con grep antes).
- [ ] `requirements-dev.txt` — Alinear versiones fijadas.
- [ ] AGENTS.md y docs — Corregir la versión de Django que se menciona (5.2 → real instalada, o subir la dep).
- [ ] `pip install -r requirements.txt` limpio (o `--dry-run`) funciona.

## Alineación env (generate_env UX)

- [x] Decisión: `env.sample` se elimina; `generate_env.py` es la única fuente de `.env` (evita drift entre ambos).
- [x] `generate_env.py` — Preguntar primero si se usa correo/LDAP/DB; solo escribir las vars del camino elegido (sin bloques comentados `# VAR=`).
- [x] `generate_env.py` — Email dev: elegir backend consola o servidor real; consola NO escribe vars de host/usuario.
- [x] `generate_env.py` — Prod: correo exige servidor real (nunca consola); DB solo postgresql/mysql (nunca sqlite3).
- [x] `generate_env.py` — Regeneración: si `.env` existe, preguntar `¿Regenerar?` con default **N** (no pisar config afinada a mano).
- [x] Eliminar `env.sample` del repo (tracked).
- [ ] Auditar `config/settings.py` — listar `os.getenv` y validar que `generate_env.py` cubre los reales (ya sin env.sample).

## Choices unificados

- [ ] Identificar choices duplicados/incompatibles en `apps/meteo/models.py` y `apps/core/models.py`.
- [ ] Crear módulo compartido (ej. `apps/meteo/choices.py` o `apps/core/choices.py`) con los choices reconciliados.
- [ ] Importar desde el módulo en ambos modelos.
- [ ] Verificar UI (filtros, admin, templates) usa los mismos valores.
- [ ] Si cambian valores en DB → data migration o documentación del impacto.

## Verificación

- [ ] `pip install -r requirements.txt` (o `--dry-run`) sin conflictos.
- [ ] `python manage.py check`
- [ ] `python manage.py test`
- [ ] Script/manual: diff de `os.getenv` de settings contra `env.sample`.
- [ ] Actualizar roadmap.md (mover 093 a Hecho al completar).
- [ ] Commit.
