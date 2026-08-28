# Spec — 002-ui-polish

Capability: `ui-polish`
Status: delta (extends current Tabler/Bootstrap 5 template baseline)
Language: English (artifact)

## Requirements

### REQ-1: Toast system MUST be single-source

The application MUST provide exactly one toast rendering implementation, defined in
`static/dist/js/utils.js` (`showToast`), and loaded via
`templates/includes/base/utils.html`.

- **MUST** render every toast through the global `showToast()` from `utils.js`.
- **MUST NOT** declare more than one element with `id="toast-container"` in the DOM.
- **MUST NOT** re-declare a `showToast` function inside any template.

Scenarios:

- **Given** a page that extends `layouts/base.html` or `layouts/base-auth.html,
  **When** the page is rendered, **Then** exactly one `#toast-container` node exists
  (the one from `templates/includes/base/utils.html`).
- **Given** `apps/commercial/templates/pages/commercial/invoice/create.html` triggers a
  validation toast, **When** the toast is shown, **Then** it uses the `utils.js` markup
  (`ti ti-circle-x` / `ti ti-circle-check`) and NOT a `bg-success`/`bg-danger` header.
- **Given** `apps/user_auth/templates/pages/user_auth/users/register.html` triggers a
  toast, **When** the toast renders, **Then** it originates from the global
  `showToast()` (no inline `function showToast` present).

### REQ-2: DataTables MUST show a processing indicator

Every DataTable initialization MUST enable a visible loading/processing state.

- **MUST** set `processing: true` in the DataTable configuration.
- **SHOULD** render the processing indicator with Tabler styling (Bootstrap spinner +
  muted label) via `.dataTables_processing` in `static/dist/css/utils.css`.

Scenarios:

- **Given** a list view built on `templates/layouts/list.html`, **When** the table
  initializes or a column is sorted/filtered, **Then** a Tabler-styled processing
  indicator is visible until rendering completes.
- **Given** the meteo forecast list DataTable, **When** it initializes, **Then** the
  same processing indicator appears.

### REQ-3: Radius and spacing MUST use Tabler utilities

Card and table containers MUST express corner radius through Tabler radius utilities
rather than inline `border-radius`.

- **MUST NOT** use `style="border-radius: …"` on `templates/layouts/list.html` or
  `apps/meteo/templates/pages/meteo/forecast/list.html`.
- **SHOULD** use `rounded-3` (or another `rounded-*` utility) instead of a hardcoded
  pixel radius.

Scenarios:

- **Given** `templates/layouts/list.html:26`, **When** the template is rendered,
  **Then** the `card-body` uses `rounded-3` and contains no inline `border-radius`.
- **Given** the meteo forecast list card (`…/forecast/list.html:44`), **When**
  rendered, **Then** the radius is a `rounded-*` utility, not an inline style.

### REQ-4: Tabler icons MUST use the `icon` sizing class

All Tabler icon glyphs MUST include the `icon` sizing class.

- **MUST** render icons as `<i class="icon ti ti-…">`.
- **MUST NOT** use a bare `<i class="ti ti-…">` (missing `icon`) or a non-standard
  class such as `icon-1`.

Scenarios:

- **Given** any template containing a Tabler icon, **When** the icon markup is
  inspected, **Then** it includes the `icon` class.
- **Given** `templates/includes/base/settings.html:282`, **When** the refresh button
  icon is rendered, **Then** it uses `icon` sizing and NOT `icon-1`.

### REQ-5: Commercial list tables MUST remain responsive (no regression)

The horizontal-scroll behavior of commercial list tables at viewports <768px MUST NOT
regress.

- **MUST** keep the `table-responsive` wrapper already present in
  `templates/layouts/list.html:26`.
- **SHOULD** verify all 6 commercial list templates still extend `layouts/list.html`.

Scenarios:

- **Given** a commercial list page (e.g. `customer/list.html`) at a 375px viewport,
  **When** the table is wider than the screen, **Then** it scrolls horizontally inside
  its card without breaking the page layout.
