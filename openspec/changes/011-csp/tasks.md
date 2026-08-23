# Tasks: Content Security Policy (CSP) via django-csp

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~60 (requirements + settings + tests) |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | ask-on-risk |
| Chain strategy | pending |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Low

## Phase 1: Implementation

- [ ] 1.1 In `requirements.txt` add `django-csp>=4.0,<5.0` (compatible with `Django==5.1.4`).
- [ ] 1.2 In `config/settings.py` insert `csp.middleware.ContentSecurityPolicyMiddleware` into `MIDDLEWARE` (after session/auth middleware).
- [ ] 1.3 In `config/settings.py` add the `CONTENT_SECURITY_POLICY` dict (see design) with `default-src 'self'`, `base-uri 'self'`, `frame-ancestors 'self'`, `object-src 'none'`, `script-src 'self' 'unsafe-inline'`, `style-src 'self' 'unsafe-inline'`, `img-src 'self' data: https://cdn.jsdelivr.net`, `font-src 'self'`, `connect-src 'self'`. Add file:line justification comments for the `'unsafe-inline'` and `cdn.jsdelivr.net` exceptions.
- [ ] 1.4 (Optional) Add `CSP_REPORT_ONLY = env.bool('CSP_REPORT_ONLY', False)` (or project-equivalent env flag) for staging observation. Confirm the env-helper dependency used by the project.

## Phase 2: Tests (strict_tdd)

- [ ] 2.1 Settings test: assert `settings.CONTENT_SECURITY_POLICY` is a dict and `settings.CONTENT_SECURITY_POLICY['default-src'] == "'self'"`.
- [ ] 2.2 Header presence: `GET` a representative page (login or home) and assert `'Content-Security-Policy' in response.headers`.
- [ ] 2.3 Directive content: assert the header contains `default-src 'self'`, `script-src 'self' 'unsafe-inline'`, `style-src 'self' 'unsafe-inline'`, `img-src 'self' data: https://cdn.jsdelivr.net`, and `object-src 'none'`.
- [ ] 2.4 (Optional, staging) With `CSP_REPORT_ONLY=True`, load a meteogram-bearing page and confirm no external-origin CSP violations are reported.

## Phase 3: Verification

- [ ] 3.1 Run the new CSP tests (`python manage.py test apps.core` or the chosen app) — all pass.
- [ ] 3.2 Run `python manage.py check` — no system check errors.
- [ ] 3.3 Manual smoke (dev): open home, a forecast/meteogram page, and the WRF models map; confirm Tabler renders, forecast symbols load (jsdelivr), and WRF images load (same-origin proxy). Browser console shows no CSP violations.

## Phase 4: Documentation

- [ ] 4.1 Note in the change log / PR that `'unsafe-inline'` is an interim exception (41 inline blocks) and that a nonce-refactor follow-up is planned.
- [ ] 4.2 Document the `CSP_REPORT_ONLY` staging toggle if implemented.

## Phase 5: Commit

- [ ] 5.1 Commit `requirements.txt`, `config/settings.py`, and the added tests with a conventional message referencing `011-csp`.
