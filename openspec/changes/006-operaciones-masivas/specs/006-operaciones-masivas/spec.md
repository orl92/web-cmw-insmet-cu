# Spec — 006-operaciones-masivas

Delta requirements for the bulk-operations capability over `SoftDeleteModel`-backed
`commercial` records. All requirements are additive; no model/migration changes.

## Requirement: BULK-SELECT-UI

The system SHALL render a per-row selection checkbox (carrying `data-uuid`) and a
header "select all" checkbox on the list views for `Customer`, `ServiceSubscription`,
`Invoice`, and `Certificate`.

- **Given** a user opens the `commercial` list view for one of the four models
  (**When** the page loads)
  **Then** each rendered row contains a checkbox with its record `uuid` in `data-uuid`
  and a header checkbox is present.
- **Given** DataTables renders all rows client-side
  (`templates/layouts/list.html:34-38`, init `:49`)
  (**When** the user paginates)
  **Then** selected `data-uuid` values persist across client-side pages.

## Requirement: BULK-EXPORT

The system SHALL export exactly the selected records as CSV, reusing the existing
`CSVExportView` column configuration.

- **Given** a user with `view_<model>` permission selects N rows
  (**When** they submit the Export bulk action via `POST`)
  **Then** the response is a CSV containing exactly those N records, using the column
  definitions from `apps/commercial/views/exports.py`
  (`CustomerCSVExportView:58`, `ServiceSubscriptionCSVExportView:99`,
  `InvoiceCSVExportView:115`, `CertificateCSVExportView:145`).
- The export dispatch MUST filter `uuid__in=uuids` in `get_queryset`
  (base `apps/core/views/exports.py:26`).

## Requirement: BULK-SOFT-DELETE

The system SHALL bulk-soft-delete selected records; it MUST NOT hard-delete.

- **Given** a user with `delete_<model>` permission selects N active rows
  (**When** they confirm the destructive bulk action via the confirmation modal `POST`)
  **Then** each target has `record_active=False` and `deleted_at` set
  (`SoftDeleteModel.delete`, `apps/core/models.py:60`), and NO row is removed from the
  database (mirrors `apps/commercial/views/customers.py:138` and
  `apps/commercial/views/certificates.py:110`).
- The bulk delete MUST NOT call `hard_delete()` (permanent delete stays single-record and
  superuser-gated: `apps/commercial/views/invoices.py:353`).

## Requirement: BULK-UPDATE

The system SHALL support a field-scoped bulk update for an explicitly enumerated set of
fields per model.

- **Given** a user with `change_<model>` permission selects N rows and submits an update
  for an allow-listed field (default `ServiceSubscription.payment_status`,
  referenced at `apps/commercial/views/invoices.py:413`)
  (**When** the update is processed)
  **Then** exactly that field is mutated on the N records and an audit entry is written.
- The system MUST reject updates to fields outside the allow-list (HTTP 400).

## Requirement: BULK-PERMISSION-GUARD

Every bulk action MUST be authorized via the project's custom Spanish permissions
(`default_permissions = ()` + `view_/add_/change_/delete_`,
e.g. `apps/commercial/models.py:244`, `:349`).

- **Given** a user lacking the required permission for the action
  (**When** they submit the bulk `POST`)
  **Then** the system returns HTTP 403 (or redirects to login) and performs no mutation.
- All bulk `POST` requests MUST be CSRF-protected
  (modal/form pattern: `apps/commercial/templates/pages/commercial/invoice/list.html`).

## Requirement: BULK-CONFIRM

Destructive bulk actions (delete, irreversible update) MUST require an explicit
confirmation before execution.

- **Given** a user triggers a destructive bulk action
  (**When** the confirmation modal is shown)
  **Then** the action executes only after the user confirms in the modal, which posts a
  CSRF-protected request to the bulk URL (modal generalized from
  `apps/commercial/templates/pages/commercial/invoice/list.html`).
- Export (non-destructive) SHOULD NOT require confirmation.

## Requirement: BULK-AUDIT

The system SHALL record each completed bulk action via `log_action`
(`apps/core/utils.py`; pattern `apps/commercial/views/invoices.py:313`), including the
actor and the count of affected UUIDs.

## Requirement: BULK-INPUT-SAFETY

- The system MUST return HTTP 400 for an unknown `action` or an empty `uuids` list.
- The system SHOULD skip unknown/non-active UUIDs rather than 404, and report processed vs
  skipped counts in the response/message.
