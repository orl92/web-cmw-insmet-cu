# Tasks · 067 Unify Warning model

- [ ] Crear `Warning` model en meteo/models/warning.py
- [ ] Registrar en admin.py
- [ ] Crear WarningForm con fieldsets condicionales
- [ ] Crear 5 vistas CRUD parametrizadas
- [ ] Registrar URLs con namespace meteo
- [ ] Crear templates warning_list, warning_form, warning_detail, warning_pdf
- [ ] Actualizar API serializer y viewset
- [ ] Data migration de EarlyWarning, TropicalCyclone, StormWarning → Warning
- [ ] Eliminar modelos legacy
- [ ] Tests
- [ ] Menú lateral con 3 entradas

## Fase 2 — Soft delete Warning (ver 090-soft-delete-integridad)

- [ ] `Warning` hereda `SoftDeleteModel` (hoy solo `models.Model`; AGENTS.md lo exige)
- [ ] `WarningDeleteView` → soft delete
- [ ] Migración `record_active`/`deleted_at` en Warning
- [ ] Verificar listado no muestre warnings borrados
