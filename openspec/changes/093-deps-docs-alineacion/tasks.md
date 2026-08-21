# Tasks — 093-deps-docs-alineacion

## Django y dependencias

- [ ] Auditar si el código usa features de Django 5.2 (grep por APIs nuevas/deprecadas). Decidir: subir a 5.2.x o mantener 5.1.4.
- [ ] `requirements.txt` — Fijar TODAS las deps con `==` (usar versiones instaladas en `.venv` como base).
- [ ] Eliminar dependencias sin uso (`dotenv`, `str2bool` — verificar con grep antes).
- [ ] `requirements-dev.txt` — Alinear versiones fijadas.
- [ ] AGENTS.md y docs — Corregir la versión de Django que se menciona (5.2 → real instalada, o subir la dep).
- [ ] `pip install -r requirements.txt` limpio (o `--dry-run`) funciona.

## Alineación env

- [ ] Auditar `config/settings.py` — listar todos los `os.getenv` con sus defaults.
- [ ] Comparar con `env.sample` y `apps/core/management/commands/generate_env.py`.
- [ ] `env.sample` — Corregir `DB_USERNAME`→`DB_USER`; dominio `SITE_URL` a `web.cmw.insmet.cu`; agregar variables faltantes (`FTP_OBS_HOST/USER/PASS`, `CORS_ALLOWED_ORIGINS`); eliminar variables que settings ignora.
- [ ] `generate_env.py` — Generar el mismo conjunto que env.sample.
- [ ] Verificar compatibilidad con `.env` existente (aceptar alias o documentar migración).

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
