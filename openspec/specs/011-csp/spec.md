# csp Specification

## Purpose

Define how the Django app emits a `Content-Security-Policy` (CSP) response header
via `django-csp`, restricting resource origins to `self` while explicitly
allowing the few exceptions the current frontend requires (inline scripts/styles
and the jsdelivr-hosted weather-symbol images). The policy must be non-breaking:
Tabler, `maps.js`, `meteogram.js`, and the forecast/amCharts JS must keep working.
`django-csp` is a new dependency.

## Requirements

### Requirement: django-csp Installed and Applied

`django-csp` MUST be added to `requirements.txt` and its
`ContentSecurityPolicyMiddleware` MUST be registered in `MIDDLEWARE` so the
`Content-Security-Policy` header is emitted on responses.

#### Scenario: Middleware is active

- GIVEN the application is configured
- WHEN `MIDDLEWARE` is inspected
- THEN it SHALL contain `csp.middleware.ContentSecurityPolicyMiddleware`
- AND `django-csp` SHALL be present in `requirements.txt`

### Requirement: CSP Policy Defined in Settings

`config/settings.py` MUST define a `CONTENT_SECURITY_POLICY` dict that sets at
least `default-src 'self'`.

#### Scenario: Minimal policy is present

- GIVEN the Django settings are loaded
- WHEN `settings.CONTENT_SECURITY_POLICY` is inspected
- THEN it SHALL be a dict
- AND `settings.CONTENT_SECURITY_POLICY['default-src']` SHALL equal `"'self'"`

### Requirement: Documented Exceptions Are Allowed

The policy MUST allow the verified, documented exceptions so the existing
frontend is not broken:

- `script-src 'self' 'unsafe-inline'` — required for the ~41 inline `<script>`
  blocks (e.g. `templates/includes/base/scripts.html:8`,
  `templates/includes/dashboard/footer.html:41`).
- `style-src 'self' 'unsafe-inline'` — required for inline `<style>` blocks
  (e.g. `templates/includes/base/head.html:15`).
- `img-src 'self' data: https://cdn.jsdelivr.net` — required for
  `static/dist/js/meteogram.js:128` and `:255` weather-symbol SVGs.

These exceptions MUST be justified with file:line references in settings
comments, and `'unsafe-inline'` MUST be recorded as an interim exception pending
a nonce-refactor follow-up.

#### Scenario: Inline scripts are permitted

- GIVEN a page with an inline `<script>` is rendered
- WHEN the browser enforces the CSP header
- THEN the inline script SHALL execute (no CSP block)
- AND `script-src` SHALL contain `'unsafe-inline'`

#### Scenario: meteogram CDN images are permitted

- GIVEN `meteogram.js` requests `https://cdn.jsdelivr.net/.../*.svg`
- WHEN the browser enforces the CSP header
- THEN the image SHALL load
- AND `img-src` SHALL contain `https://cdn.jsdelivr.net`

#### Scenario: WRF model images stay same-origin

- GIVEN `maps.js` rewrites `http://imgwrfserver.cmw.insmet.cu` to the
  `/proxy_image_modelo/` same-origin proxy
- WHEN the browser enforces the CSP header
- THEN the proxied image SHALL load under `img-src 'self'`
- AND no external host entry for `imgwrfserver.cmw.insmet.cu` SHALL be required

### Requirement: Site Remains Functional

After CSP is enforced, the public site MUST continue to work: Tabler UI, the WRF
models map (`maps.js`), the forecast meteogram (`meteogram.js` + amCharts), and
other interactive pages MUST render without CSP-blocked resources.

#### Scenario: No functional regression

- GIVEN the CSP header is enforced in production configuration
- WHEN a user loads the home page, a forecast/meteogram page, and the WRF models
  map
- THEN Tabler CSS/JS SHALL load from `'self'`
- AND forecast weather-symbol images SHALL load from `https://cdn.jsdelivr.net`
- AND WRF model images SHALL load from the same-origin proxy
- AND no required resource SHALL be blocked by the policy

### Requirement: CSP Header Present on Responses

The `Content-Security-Policy` header MUST be present on representative HTML
responses.

#### Scenario: Header is emitted

- GIVEN a client requests a page served through the Django stack
- WHEN the response is returned
- THEN the response headers SHALL contain `Content-Security-Policy`
- AND its value SHALL include `default-src 'self'`

#### Scenario: Hardening directives are present

- GIVEN the emitted header
- WHEN its value is inspected
- THEN it SHALL contain `object-src 'none'`
- AND it SHALL contain `frame-ancestors 'self'`
