# Proposal: Content Security Policy (CSP) via django-csp

## Intent

`config/settings.py` configures several `SECURE_*` hardening headers
(`SECURE_HSTS_*`, `SECURE_CONTENT_TYPE_NOSNIFF`, `SESSION_COOKIE_SECURE`,
`CSRF_COOKIE_SECURE`, `SECURE_REFERRER_POLICY`,
`SECURE_CROSS_ORIGIN_OPENER_POLICY`) but does **NOT** define a
`Content-Security-Policy` header. There is no XSS/injection mitigation at the
response layer, so a successful injection (e.g. via a rendered field or a
compromised local asset) would execute with no constraint. This change adds a
pragmatic, non-breaking CSP using the `django-csp` package and the
`CONTENT_SECURITY_POLICY` setting, restricting resource origins to `self` while
explicitly documenting the few exceptions the current frontend requires.

## Scope

### In Scope
- Add `django-csp` to `requirements.txt`.
- Add `ContentSecurityPolicyMiddleware` to `MIDDLEWARE` in `config/settings.py`.
- Define a `CONTENT_SECURITY_POLICY` dict in `config/settings.py`.
- Document, with file:line evidence, every directive that needs `'unsafe-inline'`
  or an external origin (`https://cdn.jsdelivr.net`).
- Add a test asserting the `Content-Security-Policy` header is present on
  responses.

### Out of Scope
- HSTS and other `SECURE_*` headers (already configured).
- Refactoring the ~41 inline `<script>`/`<style>` blocks to use nonces
  (nonce migration is the follow-up hardening tracked as a future change).
- CDN migration of `meteogram.js` weather symbols to local assets (separate
  optimization).
- Email/PDF templates (`*/emails/`, `*/pdf.html`, `invoice/template.html`) — these
  render in email clients / WeasyPrint, not in the browser CSP context.
- Other live SDD changes.

## Capabilities

### New Capabilities
- `csp`: Every HTML response served by the Django app carries a
  `Content-Security-Policy` header that defaults to `'self'` and only widens for
  verified, documented exceptions.

### Modified Capabilities
- None (no existing OpenSpec capability covers response security headers; this
  introduces the capability).

## Approach

1. Add `django-csp>=4.0,<5.0` to `requirements.txt`. django-csp 4.x targets
   Django 5.1 (this project pins `Django==5.1.4`) and supports the modern
   `CONTENT_SECURICY_POLICY` dict config plus `ContentSecurityPolicyMiddleware`.
2. Register `csp.middleware.ContentSecurityPolicyMiddleware` in `MIDDLEWARE`.
   It must run after `SessionMiddleware`/`AuthenticationMiddleware` (header is
   static, so placement is not order-sensitive vs. content, but keep it near the
   other security middleware).
3. Define `CONTENT_SECURITY_POLICY` in `config/settings.py` with the verified
   policy (see REQ-2 / design). The starting point restricts the essentials
   (`default-src 'self'`, `img-src 'self' data:`, `connect-src 'self'`) and adds
   the **verified** exceptions:
   - `script-src 'self' 'unsafe-inline'` — REQUIRED: 41 inline `<script>` blocks
     (e.g. `templates/includes/base/scripts.html:8` theme config,
     `templates/includes/dashboard/footer.html:41` `document.write`, and the
     create/update page scripts).
   - `style-src 'self' 'unsafe-inline'` — REQUIRED: inline `<style>` blocks
     (e.g. `templates/includes/base/head.html:15`).
   - `img-src 'self' data: https://cdn.jsdelivr.net` — REQUIRED:
     `static/dist/js/meteogram.js:128` and `:255` load weather-symbol SVGs as
     `<img>` from the jsdelivr CDN.
   - `base-uri 'self'`, `frame-ancestors 'self'`, `object-src 'none'` — free
     hardening with no breakage.
   - `font-src 'self'` — Tabler fonts are served locally by WhiteNoise.
4. Rollout safeguard: keep a `CSP_REPORT_ONLY` toggle (default `False` in
   production) so staging can observe violations before enforcing. The enforced
   policy above is already non-breaking because every real exception was found
   by static inspection.
5. The `maps.js` WRF images are NOT a CSP concern: `maps.js:85-86` strips
   `http://imgwrfserver.cmw.insmet.cu` and routes through the same-origin proxy
   `/proxy_image_modelo/`, so `img-src 'self'` covers them.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `requirements.txt` | Modified | Add `django-csp>=4.0,<5.0`. |
| `config/settings.py` | Modified | Add `MIDDLEWARE` entry + `CONTENT_SECURITY_POLICY` dict (+ optional `CSP_REPORT_ONLY`). |
| HTTP responses (all HTML) | Behavior change | New `Content-Security-Policy` header emitted by middleware. |
| `static/dist/js/meteogram.js` | Unchanged | Allowed via `img-src ... https://cdn.jsdelivr.net`. |
| `static/dist/js/maps.js` | Unchanged | Uses same-origin proxy; `img-src 'self'` suffices. |
| `templates/**` (41 inline scripts / styles) | Unchanged | Allowed via `'unsafe-inline'`. |
| `openspec/changes/011-csp/specs/011-csp/spec.md` | New | Delta spec (sdd-spec phase). |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| A missed inline/external resource breaks a page at enforcement | Low | Static inspection found all 41 inline blocks + the jsdelivr `<img>`; `CSP_REPORT_ONLY` in staging catches stragglers before prod. |
| `'unsafe-inline'` weakens script XSS protection | High (residual) | Documented as interim; nonce migration tracked as a follow-up change. `default-src 'self'` still blocks external script origins. |
| `meteogram.js` symbols fail to load | Low | `img-src` explicitly allows `https://cdn.jsdelivr.net`. |
| `django-csp` middleware ordering issue | Low | Place after session/auth middleware; header is static. |

## Rollback Plan

Revert `requirements.txt` and `config/settings.py` via `git checkout`; no
migrations. `pip install -r requirements.txt` is only needed again if the
package was installed. No static collection or schema regeneration required.

## Dependencies

- `django-csp>=4.0,<5.0` (new dependency) — compatible with `Django==5.1.4`.
- WhiteNoise already serves all local CSS/JS/fonts/images (`'self'`).

## Success Criteria

- [ ] `django-csp` is in `requirements.txt` and installed.
- [ ] `ContentSecurityPolicyMiddleware` is registered in `MIDDLEWARE`.
- [ ] `CONTENT_SECURITY_POLICY` defines at least `default-src 'self'`.
- [ ] Site works end-to-end: Tabler, `maps.js`, `meteogram.js`, forecast/amCharts
      JS render; `'unsafe-inline'` and `cdn.jsdelivr.net` are justified in-code
      with file:line references.
- [ ] A test asserts the `Content-Security-Policy` header is present on a
      representative response.
