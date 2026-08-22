# Design — 006-operaciones-masivas

## Context

The `commercial` app already has (a) soft-deletable models via `SoftDeleteModel`
(`apps/core/models.py:53`), (b) a working single-record CSV export via `CSVExportView`
(`apps/core/views/exports.py:20`), (c) single-record confirmation modals
(`apps/commercial/templates/pages/commercial/invoice/list.html`), and (d) per-model custom
Spanish permissions with `default_permissions = ()` (`apps/commercial/models.py:244`, `:349`).
What is missing is a **generic multi-record selection + bulk dispatch** layer on top of these
primitives. This design adds that layer without new models or migrations.

## Targeted models (all extend `SoftDeleteModel`)

| Model | SoftDelete base | Permissions anchor |
|---|---|---|
| `Customer` | `apps/commercial/models.py:12` | `:72` |
| `ServiceSubscription` | `:142` | `:179` |
| `Invoice` | `:210` | `:244` |
| `Certificate` | `:331` | `:349` |

`Invoice` additionally has `is_cancelled` (`apps/commercial/models.py:234`); bulk "delete"
on invoices performs the same soft path as `CancelInvoiceView`
(`apps/commercial/views/invoices.py:313`), not a hard delete.

## Component 1 — Selection UI (templates)

- DataTables renders all rows in the DOM (`templates/layouts/list.html:34-38`, init `:49`),
  so a checkbox per `<tr>` carrying `data-uuid` persists across client-side paging.
- Add a header checkbox (select-all, toggles visible rows) and a body checkbox column to the
  four list templates. No change to `layouts/list.html` itself; templates supply the extra
  `<th>`/`<td>` through their existing `{% block columns %}` / `{% block row %}`.
- A static "Bulk actions" toolbar (hidden until ≥1 row selected) renders Export / Delete /
  Update buttons. JS reads selected `data-uuid` values into the bulk form on submit.

## Component 2 — Bulk action endpoint

New `BulkActionView(LoginRequiredMixin, PermissionRequiredMixin, View)` per model, e.g.
`commercial:cliente_bulk`, `commercial:suscripcion_bulk`, `commercial:factura_bulk`,
`commercial:certificado_bulk` (URLs under `app_name='commercial'`,
`apps/commercial/urls.py:61`).

Request contract (POST, CSRF-protected):
```
{ "action": "export" | "delete" | "update", "uuids": [uuid, ...], "field"?, "value"? }
```

Dispatch:
- `export` → requires `view_<model>`; streams CSV via a `CSVExportView` subclass whose
  `get_queryset` filters `uuid__in=uuids` instead of `.all()`
  (`apps/core/views/exports.py:26`). Reuses columns from
  `apps/commercial/views/exports.py` (`CustomerCSVExportView:58`,
  `ServiceSubscriptionCSVExportView:99`, `InvoiceCSVExportView:115`,
  `CertificateCSVExportView:145`).
- `delete` → requires `delete_<model>`; for each `uuid`, `get_object_or_404(model,
  uuid=uuid, record_active=True)` then `obj.delete()` (soft; `apps/core/models.py:60`).
  Mirrors `CustomerDeleteView.delete()` (`apps/commercial/views/customers.py:138`) and
  `CertificateDeleteView.delete()` (`apps/commercial/views/certificates.py:110`).
- `update` → requires `change_<model>`; mutates ONLY an allow-listed field. Default target:
  `ServiceSubscription.payment_status` (referenced at `apps/commercial/views/invoices.py:413`).
  Input validated server-side; unknown fields or values are rejected with 400.

Safety rules (MUST):
- Never call `hard_delete()` from bulk code. Permanent deletion stays single-record and
  superuser-gated (`InvoiceHardDeleteView` `apps/commercial/views/invoices.py:353`,
  `CustomerHardDeleteView` `apps/commercial/views/customers.py:149`).
- Unknown `action` → 400. Empty `uuids` → 400. Unknown `uuid` → skipped (not 404) to avoid
  info leak; report count of processed vs skipped.
- All dispatches wrapped in a single transaction per request where the model supports it;
  partial export/delete is reported, not silently dropped.

## Component 3 — Confirmation modal (reuse)

Generalize the invoice modal
(`apps/commercial/templates/pages/commercial/invoice/list.html`
`confirmInvoiceActionModal` + `extrajs` submit) into a shared partial
(`templates/includes/bulk_confirm_modal.html`). Destructive actions (delete, irreversible
update) MUST open the modal; the modal form carries `{% csrf_token %}` and posts to the
bulk URL. Export does not require confirmation.

## Component 4 — Audit

Each completed bulk action calls `log_action`
(`apps/core/utils.py`; pattern at `apps/commercial/views/invoices.py:313`) recording the
actor, action flag, and a message with the affected UUID count.

## Files to create / modify

- Create: `apps/commercial/views/bulk.py` (`BulkActionView` + per-model subclasses).
- Modify: `apps/commercial/urls.py` (bulk routes, after `:61`).
- Modify: 4 list templates (checkbox column + bulk toolbar + JS).
- Create: `templates/includes/bulk_confirm_modal.html`.
- Create: `apps/commercial/tests/test_bulk_operations.py` (label `apps.commercial`).

## Non-goals / constraints

- No new migrations; reuses `SoftDeleteModel` and existing fields.
- No batch billing / invoice generation (separate feature).
- Reusable shape, but only `commercial` ships in this change.
