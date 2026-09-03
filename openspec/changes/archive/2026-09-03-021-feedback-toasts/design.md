# Design: 021-feedback-toasts — Django messages as toasts

## Technical Approach

Replace the `{% if messages %}` alert blocks in `dashboard.html` (L36–49) and `home.html` (L28–41) with inline `<script>` tags calling the existing `showToast()` from `utils.js`. Zero Python changes. Django's session-stored messages are iterated server-side; each message emits a deferred JS call that renders a Bootstrap toast in `#toast-container`.

## Architecture Decisions

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Inline `<script>` per message vs. JSON array + single loop | Inline simpler (no new JS, no JSON escaping); matches existing `showToast` usage | **Inline `<script>`** |
| Modify `showToast` to accept raw HTML | Adds XSS surface; `safeMessage` escape is a second defense layer | Keep `showToast` untouched |
| Put toast logic in `utils.html` (shared) | Would need template tag or context processor; messages only in dashboard+home layouts | **Template block in each layout** |
| New JS file for toast init | Extra HTTP request, bundler not allowed | Reuse `utils.js` as-is |

## Data Flow

    View calls messages.success("Guardado")
              │
              ▼
    Django stores message in session (stored=True)
              │
              ▼
    View returns redirect → 302 → browser GETs new page
              │
              ▼
    Template renders: {% for message in messages %}
              │
              ▼
    <script> → deferred DOMContentLoaded → showToast("Guardado", "success")
              │
              ▼
    showToast reads #toast-container (from utils.html, already in DOM)
              │
              ▼
    Bootstrap.Toast renders floating toast, autohide 5s

## Replacement Block

**Files**: `templates/layouts/dashboard.html` (replace L36–49), `templates/layouts/home.html` (replace L28–41).

Both get identical markup:

```django
{% if messages %}
  <script>
    document.addEventListener('DOMContentLoaded', function () {
      var _toastMap = {success: "success", error: "danger", warning: "warning", info: "info"};
      {% for message in messages %}
        showToast(
          "{{ message|escapejs }}",
          {% if "danger" in message.extra_tags %}"danger"{% else %}_toastMap["{{ message.level_tag|escapejs }}"] || "info"{% endif %},
          5000
        );
      {% endfor %}
    });
  </script>
{% endif %}
```

**Tag mapping** (Django `level_tag` → toast type):

| Django level_tag | Toast type | Notes |
|------------------|-----------|-------|
| `success` | `"success"` | ti-circle-check icon |
| `error` | `"danger"` | ti-circle-x; maps to Bootstrap danger class |
| `warning` | `"warning"` | ti-alert-triangle icon |
| `info` | `"info"` | ti-info-circle icon |
| any + `extra_tags` contains `"danger"` | `"danger"` | 6 existing calls; overrides level_tag |

## Why DOMContentLoaded Is Required

`base.html` renders `{% block page %}` (dashboard/home content) at L25, then includes `utils.html` at L30. `utils.html` loads `utils.js` which defines `showToast`. Inline scripts inside the page body execute when the browser parses them — **before** `utils.js` loads. Wrapping in `DOMContentLoaded` defers execution until after all scripts load.

## Reuse

- **No duplicate `#toast-container`**: `utils.html` (included in `base.html:30` and `base-auth.html:27`) already provides the container. The new block only emits `<script>` calls.
- `showToast` + `#toast-container` already work for maintenance toggle — same mechanism, no new CSS/JS/DOM.
- `base.html` is extended by both `dashboard.html` and `home.html`.

## Security — Double Escape Layer

1. **Template**: `{{ message|escapejs }}` and `{{ message.level_tag|escapejs }}` escape `'`, `"`, `\`, `</`, `>`, newlines → prevents breaking JS string literal and `</script>` injection.
2. **JS**: `showToast` applies `safeMessage` (HTML-entity escapes `&`, `<`, `>`, `"`, `'`) → second XSS defense before DOM insertion.
3. **`</script>` scenario**: `escapejs` converts `<` → `\u003C`, `>` → `\u003E`. JS parser never sees a closing tag. Even if bypassed, `safeMessage` HTML-encodes the angle brackets.
4. **No `safe` filter**: never `|safe` on message content.
5. **`level_tag` injection**: Django guarantees `level_tag` is one of `debug|info|success|warning|error`. `escapejs` provides defense-in-depth regardless.

## Load Order

```
base.html
  {% block page %}           ← dashboard.html / home.html body content
    └─ <script> showToast…   ← inline (deferred via DOMContentLoaded)
  scripts.html (L29)         ← tabler.min.js, jquery, bootstrap, popper
  utils.html (L30)           ← #toast-container div + utils.js (defines showToast)
  {% block extrajs %} (L32)  ← page-specific scripts
```

DOMContentLoaded fires after the full HTML is parsed and all scripts (including `utils.js`) have executed. `#toast-container` is in the DOM when `showToast` queries `getElementById`.

## Compatibility

| Component | Impact |
|-----------|--------|
| `initAutoDismissAlerts` | Untouched. Targets `.alert.alert-dismissible` — no such elements from messages after this change. |
| Existing alerts in other templates | None. Only `dashboard.html` and `home.html` have the messages block. |
| Middleware redirect messages | `CheckUserProfileMiddleware`, `MaintenanceModeMiddleware`, login/logout store messages in session. Survive redirects, render on next GET via the new block. |
| `extra_tags='danger'` calls | 6 occurrences in views (logo/favicon/avatar delete, publication errors). Override logic handles these. |
| `base-auth.html` | No messages block currently; no change needed. |

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Template | Toast block renders for each level | `render_to_string` with messages context; assert `showToast(` present, `alert alert-` absent |
| Template | `escapejs` prevents `</script>` injection | Message with `</script><script>alert(1)</script>` → no raw `</script>` in output |
| Template | `extra_tags='danger'` override | Message with `extra_tags='danger'` → `"danger"` in toast call |
| Template | No `.alert` elements from messages | Assert `class="alert` absent from response |
| Integration | Middleware messages survive redirect | Simulate redirect scenario → assert toast in response |

Test file: new `apps/core/tests/test_feedback_toasts.py`.

## Threat Matrix

N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary.

## Migration / Rollout

No migration required. No data changes. No feature flags. Pure template-level change, effective on next page load.

## Files to Modify

| File | Action | Description |
|------|--------|-------------|
| `templates/layouts/dashboard.html` | Modify (L36–49) | Replace alert block with toast script block |
| `templates/layouts/home.html` | Modify (L28–41) | Replace alert block with toast script block |

No Python files modified. No new files created (except tests).

## Open Questions

- None. All technical decisions resolved by existing `showToast` and Django messages API.
