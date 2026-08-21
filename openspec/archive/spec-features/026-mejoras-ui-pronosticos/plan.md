# Plan · 026 · Mejoras UI pronósticos

## Enfoque técnico

Solo se modifican templates; no hay cambios de modelo, vistas, URLs, JS ni base de datos.

### Archivos a modificar

| Archivo | Cambio |
|---|---|
| `templates/pages/dashboard/pronosticos/pronosticos.html` | Reestructurar title_actions y content blocks: botones editar/eliminar en header, tablas vacías en `{% else %}`, btn-icon, btn-sm |
| `templates/pages/dashboard/pronosticos/form_pronostico.html` | `col` → `col-12 col-lg` para que tarjetas extendido apilen en móvil |

### Sin cambios en

- Modelos, vistas, URLs, JS
- Base de datos o migraciones
- API endpoints
