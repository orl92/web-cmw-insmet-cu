# 093 · Alineación de dependencias y documentación — Plan

## Enfoque

4 frentes de alineación. El de mayor impacto es fijar Django/deps (afecta CI y reproducibilidad). El de env requiere auditar settings variable por variable.

## Implementación

1. **Django/deps**:
   - Verificar si el código usa features de Django 5.2 (si no, mantener 5.1.4 y corregir docs).
   - Fijar todas las deps con `==` (versiones actuales instaladas en `.venv`).
   - Eliminar `dotenv`/`str2bool` si no se usan (grep).
   - Actualizar AGENTS.md y cualquier doc que diga 5.2.
2. **Env**:
   - Auditar `config/settings.py` completo: listar todos los `os.getenv`.
   - Comparar con `env.sample` y `generate_env.py`; alinear (nombres, default, dominio).
   - Agregar variables faltantes (FTP_OBS_*, CORS_ALLOWED_ORIGINS).
   - Eliminar variables que settings no lee.
3. **Choices**:
   - Identificar los choices duplicados en `apps/meteo/models.py` y `apps/core/models.py`.
   - Crear módulo compartido de choices; importar en ambos.
   - Verificar UI/admin usan los mismos.

## Riesgos

- Subir Django 5.1.4→5.2.x puede romper features deprecadas → si el código es 5.1-compatible, documentar 5.1.4 como soportado (menor riesgo). Decidir con evidencia.
- Fijar deps con `==` puede romper el install si una dep transitiva exige otra versión → probar `pip install -r requirements.txt` limpio.
- Cambiar variables de env puede romper el `.env` actual del usuario → mantener compatibilidad (aceptar alias `DB_USERNAME`→`DB_USER` con fallback) o documentar la migración.
- Unificar choices puede cambiar valores en DB si difieren → data migration si es necesario (o documentar).

## Verificación

- `pip install -r requirements.txt` limpio (venv nuevo o `--dry-run`).
- `python manage.py check`
- `python manage.py test`
- Script: extraer `os.getenv` de settings y diff contra env.sample (check manual).
- `python manage.py makemigrations --check --dry-run`.
