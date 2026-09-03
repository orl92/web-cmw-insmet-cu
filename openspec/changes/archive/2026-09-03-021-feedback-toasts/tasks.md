# Tasks: 021-feedback-toasts — Django messages as toasts

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~80–120 |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | ask-on-risk |
| Chain strategy | pending |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Low

## Phase 1: Template replacement

- [x] 1.1 Replace `{% if messages %}` block (L36–49) in `templates/layouts/dashboard.html` with the toast `<script>` block from design.md (DOMContentLoaded wrapper, `_toastMap`, `showToast`, `escapejs`). Verify `#toast-container` is NOT duplicated.
- [x] 1.2 Replace `{% if messages %}` block (L28–41) in `templates/layouts/home.html` with identical toast `<script>` block. Verify no `.alert.alert-*` remnants from messages.

## Phase 2: Tests

- [x] 2.1 Create `apps/core/tests/test_feedback_toasts.py`. RED: write test `test_success_renders_toast` — `render_to_string` on `dashboard.html` with a single `messages.SUCCESS` context → assert `showToast(` present, `.alert` absent.
- [x] 2.2 RED: `test_error_maps_to_danger` — `messages.ERROR` → output contains `"danger"` type.
- [x] 2.3 RED: `test_warning_maps_to_warning` — `messages.WARNING` → `"warning"` type.
- [x] 2.4 RED: `test_info_maps_to_info` — `messages.INFO` → `"info"` type.
- [x] 2.5 RED: `test_extra_tags_danger_overrides_success` — `level_tag=success` + `extra_tags='danger'` → `"danger"` in toast call.
- [x] 2.6 RED: `test_escapejs_prevents_script_injection` — message contains `</script><script>alert(1)</script>` → no raw `</script>` in output.
- [x] 2.7 RED: `test_no_alert_class_from_messages` — render with messages → `class="alert` absent from output.
- [x] 2.8 RED: `test_redirect_message_survives` — simulate redirect-stored message (FallbackStorage on next request) → response contains `showToast(`.
- [x] 2.9 GREEN: Run `python manage.py test apps.core.tests.test_feedback_toasts` — all tests pass (9 tests OK).

## Phase 3: Verification

- [x] 3.1 `python manage.py check` — 0 issues.
- [x] 3.2 `python manage.py test apps.core` — full core suite green (163 tests OK).
- [x] 3.3 `djlint . --reformat --check && djlint . --lint` — my templates clean (2/2). Note: full-repo run flags 1 pre-existing vendored file `staticfiles/drf_spectacular_sidecar/swagger-ui-dist/oauth2-redirect.html`, unrelated to 021.
- [x] 3.4 `ruff check .` — no lint issues.
