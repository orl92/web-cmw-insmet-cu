# Política de Seguridad

## Versiones soportadas

El proyecto se desarrolla sobre Django 5.2. Solo la versión más reciente de `main` recibe actualizaciones de seguridad activas. La política se aplica tanto al código del repositorio como a las dependencias declaradas en `requirements.txt`.

| Rama | Soporte |
| --- | --- |
| `main` (última) | ✅ Soporte activo |
| Tags/versiones anteriores | ❌ Sin soporte |

## Reportar una vulnerabilidad

Las vulnerabilidades se gestionan de forma **privada** hasta su resolución. No abras issues públicos con detalles de seguridad.

1. **Reporta a través de GitHub Security Advisories** si es posible:
   `https://github.com/orl92/web-cmw-insmet-cu/security/advisories`
2. O contacta por correo institucional: `admin@cmw.insmet.cu`

### Qué incluir en el reporte

- Tipo de vulnerabilidad (XSS, SQLi, CSRF, exposición de datos, etc.).
- Componente afectado (app, vista, template, endpoint API, dependencia).
- Versión/commit donde se reproduce.
- Pasos de reproducción o prueba de concepto (sin datos reales de producción).
- Impacto esperado.

### Expectativas

- Confirmación de recepción: en un plazo razonable de **5 días hábiles**.
- Actualización de estado: a medida que se investiga y se prepara el fix.
- Divulgación pública coordinada: tras publicar la corrección en `main`.

## Alcance

Se consideran dentro del alcance: el código del repositorio (`apps/`, `config/`), los templates Django, los endpoints de la API REST (`/api/`) y las dependencias de `requirements.txt`.

**Fuera de alcance:** configuraciones del servidor (Nginx, Gunicorn, Supervisor), credenciales de producción, y vulnerabilidades en infraestructura de terceros (GitHub Actions, hosts).

## Buenas prácticas del proyecto

- El CI ejecuta `pip-audit` (vulnerabilidades de dependencias) y `bandit` (SAST estático) en cada push/PR.
- `requirements.txt` solo contiene dependencias de runtime; las de desarrollo viven en `requirements-dev.txt`.
- Dependabot mantiene las dependencias actualizadas con auto-merge solo para updates menores/patch; los majors requieren revisión manual.
