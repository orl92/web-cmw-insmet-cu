# Feature 093 · Alineación de dependencias y documentación

## Motivación

Auditoría de consistencia encontró deudas técnicas de alineación:

1. **`Django==5.1.4` en `requirements.txt` pero la documentación y CI dicen 5.2** — AGENTS.md, pyproject (`target-version` no aplica, pero el CI usa Python 3.12), y el mensaje de la feature 083 hablan de Django 5.2. La versión instalada es 5.1.4. Además `requirements.txt` mezcla versiones no fijadas (riesgo de drift).
2. **`env.sample` desalineado con `generate_env.py` y con settings** — la auditoría encontró: `DB_USERNAME` vs `DB_USER` (settings lee `DB_USER`), dominio `cmw.insmet.cu` vs `web.cmw.insmet.cu` en `SITE_URL`, variables listadas en env.sample que settings ignora (y viceversa: variables que settings usa y no están en env.sample). `generate_env.py` tampoco las genera coherentemente.
3. **Choices meteorológicos duplicados e incompatibles** — `apps/meteo/models.py` y `apps/core/models.py` definen choices de `warning_type`/estados con nombres/valores distintos; la UI y los filtros pueden divergir. La feature 067 centralizó Warning pero los choices siguen dispersos.
4. **Dependencias no fijadas** — `requirements.txt` tiene algunas con `>=`/`~=` y otras fijas; `pip-audit` en CI no puede verificar reproducibilidad. `dotenv` y `str2bool` (o similares) instalados pero sin uso.

## Solución

### 1. Versionado de Django y deps
- Decidir y fijar la versión de Django: si el código usa features de 5.2, subir a la última 5.2.x; si no, **documentar 5.1.4 como la versión soportada** y corregir la doc/CI para que diga 5.1.4.
- Fijar TODAS las dependencias con `==` (o rangos estrechos) en `requirements.txt`.
- Eliminar dependencias sin uso (`dotenv`, `str2bool` si no se usan).
- Actualizar `requirements-dev.txt` coherentemente.

### 2. Alineación env
- Definir `env.sample` y `generate_env.py` a partir de los `os.getenv` reales de `config/settings.py` (auditar cada variable).
- Corregir `DB_USERNAME`→`DB_USER`, dominio `SITE_URL`, y agregar variables faltantes (ej. `FTP_OBS_*` de 088, `CORS_ALLOWED_ORIGINS` de 065).
- Eliminar variables fantasma (que settings no lee).

### 3. Choices unificados
- Centralizar los choices de warning/estado en un módulo compartido (ej. `apps/meteo/choices.py` o `apps/core/choices.py`) y hacer que ambos modelos importen de ahí.
- Reconciliar valores/etiquetas; verificar que la UI (filtros, admin) use los mismos.

## Criterios de aceptación

- [ ] `requirements.txt` fija TODAS las deps (sin `>=` sueltos) y la versión de Django coincide con la documentación.
- [ ] AGENTS.md/CI/documentación dicen la versión real instalada.
- [ ] `env.sample` cubre exactamente las variables que settings lee (auditado).
- [ ] `generate_env.py` genera el mismo conjunto.
- [ ] Choices de warning/estado unificados en un solo lugar.
- [ ] Dependencias sin uso eliminadas.
- [ ] `python manage.py check` y `python manage.py test` pasan.
