---
name: django-expert
description: "Trigger: Django, DRF, ORM, modelos, queries, auth, tests, performance Django. Guía experta de desarrollo Django/DRF con las convenciones de este proyecto."
license: Apache-2.0
metadata:
  author: "yoelvismr"
  version: "1.0"
---

# Skill: django-expert

## Activation Contract

Cargar al escribir o revisar modelos, vistas, serializers, queries, autenticación, tests o problemas de performance Django/DRF en `apps/`.

## Hard Rules

- Apps viven en `apps/`; importar siempre `from apps.<app>.models import ...`.
- Modelos de negocio: `default_permissions = ()` + permisos custom `view_*`, `add_*`, `change_*`, `delete_*` en español.
- `FileHandlerMixin` + `file_fields` obligatorio en todo modelo con FileField/ImageField.
- Soft delete: usar el manager por defecto (filtra `record_active=True`), nunca `all_objects`.
- URLs de modelos con UUIDField usan kwarg `uuid` (nunca `pk`).
- Vistas con DataTables cargan todos los registros (pagina el cliente); el resto usa `paginate_by = 20`.
- DRF: `DjangoModelPermissionsOrAnonReadOnly`; schema via drf-spectacular.
- Tests: label completo `apps.<app>` (Django 5.2 no resuelve labels cortos).

## Decision Gates

| Situación | Acción |
|---|---|
| Query N+1 o lento | `select_related`/`prefetch_related`; verificar con `connection.queries` en test |
| Borrado lógico | `record_active=True` en manager por defecto |
| Archivos subidos | `FileHandlerMixin` con `file_fields` |
| Migraciones | Generar y NO versionar (`.gitignore`) |

## Execution Steps

1. Leer el modelo y sus relaciones antes de tocar queries.
2. Aplicar las convenciones del proyecto (permisos, mixins, UUID).
3. Escribir/ajustar tests con el label completo.
4. Verificar: `python manage.py check && python manage.py test apps.<app>`.

## Output Contract

- Código que respeta las convenciones del proyecto.
- Test del cambio si no existía.
- Comando de verificación ejecutado y su resultado.

## References

- `../../AGENTS.md` — convenciones del proyecto (apps, permisos, URLs, tests).
