# Tasks — 006-operaciones-masivas

## Phase 0 — Grounding & contracts
- [x] Confirm `SoftDeleteModel.delete` soft semantics (`apps/core/models.py:60`) and that no
      targeted model overrides delete to hard-delete.
- [x] Confirm CSV column configs exist for the four models
      (`apps/commercial/views/exports.py:58,99,115,145`).

## Phase 1 — Bulk action endpoint
- [x] Create `apps/commercial/views/bulk.py` with `BulkActionView` and per-model subclasses
      (Customer, ServiceSubscription, Invoice, Certificate).
- [x] Export dispatch: subclass `CSVExportView` and filter `uuid__in=uuids`
      (`apps/core/views/exports.py:26`).
- [x] Delete dispatch: soft-delete via `obj.delete()` (`apps/core/models.py:60`), require
      `delete_<model>`, skip unknown UUIDs.
- [x] Update dispatch: allow-listed field only (default `ServiceSubscription.payment_status`,
      `apps/commercial/views/invoices.py:413`), require `change_<model>`, validate input.
- [x] Enforce CSRF + `PermissionRequiredMixin`; reject unknown action / empty uuids (400).

## Phase 2 — URLs
- [x] Register bulk routes under `app_name='commercial'` (`apps/commercial/urls.py:61`),
      e.g. `<uuid:uuid>/bulk/` named `<model>_bulk`.

## Phase 3 — Selection UI (templates)
- [x] Add checkbox column (header select-all + per-row `data-uuid`) to the four list
      templates, keeping `{% extends 'layouts/list.html' %}`.
- [x] Add bulk action toolbar (Export / Delete / Update) shown when ≥1 row selected.
- [x] Wire JS to collect selected UUIDs into the bulk form on submit.

## Phase 4 — Confirmation modal
- [x] Extract invoice modal into `templates/includes/bulk_confirm_modal.html`
      (pattern: `apps/commercial/templates/pages/commercial/invoice/list.html`).
- [x] Require modal confirmation for delete / irreversible update; CSRF-protected POST.

## Phase 5 — Audit
- [x] Call `log_action` (`apps/core/utils.py`) for each completed bulk action.

## Phase 6 — Tests & verification
- [x] Create `apps/commercial/tests/test_bulk_operations.py` (label `apps.commercial`):
      export returns exactly selected rows; bulk delete sets `record_active=False` (no
      hard delete); permission denial returns 403; update rejects non-allow-listed fields.
- [x] Run `python manage.py check && python manage.py test apps.commercial`.
