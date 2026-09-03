# feedback-toasts Specification

change: 021-feedback-toasts
requirement: feedback-toasts
version: 1.0.0

## Purpose

Unify all Django `messages.*` feedback into toast notifications rendered server-side
via `showToast()` in `#toast-container`. Replaces the current `.alert` blocks in
`dashboard.html` and `home.html` with inline `<script>` tags that emit toast markup
on page load — no changes to Python views, middleware, or the `messages` API.

---

## Requirements

### Requirement: Django messages MUST render as toasts, not fixed alerts

Every Django message produced by `django.contrib.messages` MUST be rendered as a toast
notification inside `#toast-container` via a server-side `<script>` that calls
`showToast(msg, type, 5000)`. The existing `.alert.alert-*` blocks in
`dashboard.html` and `home.html` MUST be removed.

- GIVEN a view calls `messages.success(request, "Saved")`
- WHEN the response page renders
- THEN the HTML SHALL contain a `<script>` block calling `showToast("Saved", "success", 5000)`
- AND the HTML SHALL NOT contain `.alert.alert-success` for that message
- AND exactly ONE `#toast-container` node SHALL exist in the DOM (from `utils.html`)

#### SCENARIO success-toast-visible => formally verifying that a messages.success call
from any view produces a toast in #toast-container with type "success" on the next
page load, and no .alert element is rendered for that message.

#### SCENARIO single-toast-container => formally verifying that the DOM contains
exactly one element with id="toast-container", sourced from
templates/includes/base/utils.html, with no duplicate injected by the toast
rendering logic.

---

### Requirement: Message type mapping MUST follow level_tag with danger override

The toast type MUST be derived from `message.level_tag` with this mapping:
`success` → `"success"`, `error` → `"danger"`, `warning` → `"warning"`,
`info` → `"info"`. If `message.extra_tags` contains the string `"danger"`,
the toast type MUST be forced to `"danger"` regardless of `level_tag`.

- GIVEN a view calls `messages.error(request, "Failed")`
- WHEN the toast script is emitted
- THEN the call SHALL be `showToast("Failed", "danger", 5000)`

- GIVEN a view calls `messages.warning(request, "Check input")`
- WHEN the toast script is emitted
- THEN the call SHALL be `showToast("Check input", "warning", 5000)`

- GIVEN a view calls `messages.info(request, "Note")`
- WHEN the toast script is emitted
- THEN the call SHALL be `showToast("Note", "info", 5000)`

#### SCENARIO error-maps-to-danger => formally verifying that messages.error produces
a toast with type "danger", not "error".

#### SCENARIO warning-maps-to-warning => formally verifying that messages.warning
produces a toast with type "warning".

#### SCENARIO info-maps-to-info => formally verifying that messages.info produces a
toast with type "info".

#### SCENARIO extra-danger-overrides-success => formally verifying that a message with
level_tag "success" but extra_tags containing "danger" produces a toast with type
"danger", overriding the level_tag mapping.

---

### Requirement: Toast script text MUST be XSS-safe via escapejs

The message body, `level_tag`, and `tags` values MUST be passed through Django's
`escapejs` template filter before being embedded in inline `<script>` tags. This
prevents broken `<script>` tags, unescaped quotes, and XSS payloads from
escaping the toast context.

- GIVEN a view calls `messages.success(request, "User said '</script><script>alert(1)</script>'")`
- WHEN the HTML is inspected
- THEN the `<script>` block SHALL contain the escaped representation of the message
- AND no raw `</script>` closing tag SHALL appear inside the inline script body

#### SCENARIO xss-safe-escaping => formally verifying that a message containing
single quotes, double quotes, angle brackets, and the literal string "</script>"
does not break the inline <script> block and does not introduce XSS. The escaped
output MUST pass through Django's escapejs filter.

---

### Requirement: Messages from redirects MUST survive and appear on next load

Django messages stored in the session after a redirect (login, logout, profile
incomplete, maintenance toggle) MUST be rendered as toasts on the subsequent page
load. The implementation MUST NOT alter the message storage or retrieval mechanism
— only the template rendering changes.

- GIVEN a user submits login and is redirected to the dashboard
- WHEN the dashboard page renders after redirect
- THEN any messages added by the view (e.g. "Bienvenido") SHALL appear as toasts

- GIVEN a superuser activates maintenance mode and is redirected
- WHEN the next page renders
- THEN the maintenance confirmation message SHALL appear as a toast

#### SCENARIO redirect-survives-session => formally verifying that a message stored
in the session during a redirect (e.g. login OK, profile incomplete) is rendered
as a toast on the page loaded after the redirect, confirming no data loss.

---

### Requirement: Toasts MUST auto-dismiss and provide manual close

Every toast emitted by the server-side `<script>` blocks MUST auto-dismiss after
5000 ms and include a close button, consistent with the existing `showToast()`
behavior in `utils.js`.

- GIVEN a message is rendered as a toast
- WHEN the toast appears in the DOM
- THEN it SHALL auto-hide after approximately 5 seconds
- AND it SHALL include a close button allowing manual dismissal

#### SCENARIO auto-dismiss-and-close => formally verifying that the toast element
produced by showToast has autohide enabled and a visible close button, matching
the existing showToast contract in utils.js.

---

### Requirement: No changes to Python messages API, views, or middleware

This change MUST NOT modify any Python code: `messages.*` calls in views,
`middleware.py`, or the `django.contrib.messages` framework configuration. The
change is strictly template-layer (rendering).

- GIVEN the git diff for this change
- WHEN Python files are inspected
- THEN no file under `apps/` or `config/` SHALL show modifications to
  `messages.success`, `messages.error`, `messages.warning`, `messages.info`,
  or the message middleware

#### SCENARIO python-code-untouched => formally verifying that the implementation
change is confined to template files (dashboard.html, home.html) and does not
touch any Python source, middleware configuration, or the messages API usage.

---

### Requirement: Template formatting MUST pass djlint

All templates modified by this change MUST pass `djlint . --reformat --check` and
`djlint . --lint` without errors. Indentation SHALL be 2 spaces per project
convention.

#### SCENARIO djlint-clean => formally verifying that the modified templates
dashboard.html and home.html pass djlint reformat check and lint without errors
after the change is applied.
