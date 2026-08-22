# Proposal

## Intent

Provide a reusable, secure UI for **bulk operations over business records** in the
`commercial` app (and reusable for any `SoftDeleteModel`-backed list view): multi-record
selection, bulk export, bulk soft-delete, and a scoped bulk update. Every destructive
action MUST go through an explicit confirmation step and MUST respect Django's custom
Spanish permissions, and bulk delete MUST use soft-delete semantics — never
hard-delete.

This change reframes the legacy "batch billing / ZIP export" framing into a generic,
defense-in-depth bulk-operations capability built on the patterns that already exist in
the codebase.

## Scope In

- A selectable checkbox column (with header "select all") on DataTables-backed list
  views for `Customer`, `ServiceSubscription`, `Invoice`, and `Certificate`.
- A bulk action bar that submits the selected UUIDs (`POST`) to a per-model bulk action
  endpoint.
- Bulk **export**: stream a CSV of the selected records, reusing the existing
  `CSVExportView` column configuration (`apps/core/views/exports.py:20`).
- Bulk **soft-delete**: set `record_active=False` via `SoftDeleteModel.delete`
  (`apps/core/models.py:60`), guarded by the model's `delete_<model>` custom permission.
- Bulk **update**: a field-scoped update (e.g. `payment_status` on `ServiceSubscription`)
  guarded by the model's `change_<model>` custom permission.
- A shared confirmation modal for destructive bulk actions (delete / irreversible
  update), reusing the single-record modal pattern already proven in
  `apps/commercial/templates/pages/commercial/invoice/list.html`.

## Scope Out

- Hard-delete in bulk (permanent deletion remains superuser-only and single-record only,
  e.g. `InvoiceHardDeleteView` `apps/commercial/views/invoices.py:353`).
- Arbitrary field mass-edits; bulk update is restricted to an explicitly enumerated set
  of safe fields per model.
- Batch invoice generation / "bill selected subscriptions" (out of scope; a separate
  feature if needed).
- Bulk operations outside `commercial` (reusable design, but only `commercial` ships in
  this change).

## Approach

Grounded in existing code:

1. **Selection UI** — DataTables already renders every row in the DOM
   (`templates/layouts/list.html:34-38` loops `objects`; DataTables init at `:49`). Because
   all records are client-side, per-row checkboxes carrying `data-uuid` survive client-side
   pagination. Add a checkbox `<th>`/`<td>` to the four list templates
   (`apps/commercial/templates/pages/commercial/{customer,subscription,invoice,certificate}/list.html`),
   keeping the `{% extends 'layouts/list.html' %}` contract.
2. **Bulk endpoint** — Add a `BulkActionView(LoginRequiredMixin, PermissionRequiredMixin, View)`
   per targeted model (pattern: `CancelInvoiceView` `apps/commercial/views/invoices.py:313`)
   that accepts `POST {action, uuids[], csrf}` and dispatches to export / delete / update.
   Permissions use the project's 4 custom Spanish perms
   (`default_permissions = ()` + `view_/add_/change_/delete_`, e.g.
   `apps/commercial/models.py:244` for Invoice, `:349` for Certificate).
3. **Bulk export** — Subclass/reuse `CSVExportView` (`apps/core/views/exports.py:20`); override
   `get_queryset` to `self.model.objects.filter(uuid__in=uuids)` instead of `.all()` (`:26`).
   Reuse the existing column definitions from `apps/commercial/views/exports.py`
   (`CustomerCSVExportView:58`, `ServiceSubscriptionCSVExportView:99`,
   `InvoiceCSVExportView:115`, `CertificateCSVExportView:145`).
4. **Bulk soft-delete** — For each `uuid`, call `obj.delete()` (the `SoftDeleteModel.delete`
   override at `apps/core/models.py:60` sets `record_active=False` + `deleted_at`, NOT a
   hard delete). Mirror `CustomerDeleteView.delete()` (`apps/commercial/views/customers.py:138`)
   and `CertificateDeleteView.delete()` (`apps/commercial/views/certificates.py:110`).
   Require `PermissionRequiredMixin` with `delete_<model>`; never call `hard_delete()`.
5. **Bulk update** — Field-scoped, validated against an allow-list; requires
   `change_<model>`. Example target: `ServiceSubscription.payment_status`
   (used at `apps/commercial/views/invoices.py:413`).
6. **Confirmation modal** — Generalize the invoice modal
   (`apps/commercial/templates/pages/commercial/invoice/list.html` `confirmInvoiceActionModal`
   block + `extrajs` submit script) into a shared partial wired to the bulk form; destructive
   actions MUST confirm before `POST`. CSRF token required
   (`{% csrf_token %}` form, as in the invoice template).
7. **Audit** — Log each bulk action via `log_action`
   (`apps/core/utils.py`, used by `CancelInvoiceView` `apps/commercial/views/invoices.py:313`).
8. **URLs** — Register under `app_name = 'commercial'`
   (`apps/commercial/urls.py:61`) with UUID kwargs, e.g.
   `<uuid:uuid>/bulk/` named `<model>_bulk`.

## Acceptance Criteria

- [ ] Checkbox column (select-all header + per-row `data-uuid`) present on Customer,
      ServiceSubscription, Invoice, and Certificate list views.
- [ ] Selecting N rows and choosing **Export** downloads a CSV containing exactly those N
      records, using existing column config.
- [ ] Selecting N rows and choosing **Delete** soft-deletes them: each target has
      `record_active=False` and `deleted_at` set; no row is hard-deleted.
- [ ] Bulk delete/update is blocked for users lacking `delete_<model>` / `change_<model>`
      (HTTP 403 / redirect), enforced by `PermissionRequiredMixin`.
- [ ] Destructive bulk actions require an explicit confirmation modal submit (CSRF-protected).
- [ ] Bulk update only mutates the enumerated allow-list fields and validates input.
- [ ] Every bulk action writes an audit entry via `log_action`.
- [ ] `python manage.py check && python manage.py test apps.commercial` passes.

## Rollback

- Remove the bulk action views/URLs and the checkbox/modal template additions.
- No model or migration changes are introduced (the capability reuses `SoftDeleteModel` and
  existing fields), so rollback requires no `migrate` and leaves no schema residue.
- CSV column config already exists and is preserved; only the new bulk dispatch is removed.
