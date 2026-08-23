# Design: Content Security Policy (CSP) via django-csp

## Technical Approach

Install `django-csp` and register `ContentSecurityPolicyMiddleware` in
`config/settings.py`. Define the policy as a `CONTENT_SECURITY_POLICY` dict
(django-csp 4.x modern config). The middleware emits the
`Content-Security-Policy` header on every response. The policy is **non-breaking
by construction**: it was derived from a full static audit of the frontend
(inline scripts/styles + external subresource loads), so every required
exception is already encoded. A `CSP_REPORT_ONLY` toggle lets staging observe
violations without enforcement.

## Architecture Decisions

| Decision | Options | Tradeoff | Chosen |
|----------|---------|----------|--------|
| Policy config style | `CONTENT_SECURITY_POLICY` dict (django-csp 4.x) vs legacy `CSP_DEFAULT_SRC` flat settings | Dict is the supported form for Django 5.1 and groups the policy in one readable block. Legacy flat settings are deprecated. | `CONTENT_SECURITY_POLICY` dict |
| Handling inline code | (a) report-only first, (b) `'unsafe-inline'` interim, (c) nonce refactor | (a) alone gives no protection in prod; (c) is the real hardening but touches 41 templates — large, risky blast radius. (b) is non-breaking today and protects against *external* injection immediately. | (b) enforced now, (c) tracked as follow-up |
| External image origin | Block all external vs allow `cdn.jsdelivr.net` | `meteogram.js:128,255` loads weather-symbol SVGs from jsdelivr as `<img>`; blocking would hide forecast symbols. Allowing only that host keeps `default-src 'self'` for everything else. | Allow `https://cdn.jsdelivr.net` in `img-src` only |
| Rollout | Enforce immediately vs report-only first | Static audit already found all exceptions, so enforce is safe; report-only is kept as an opt-in staging safeguard, not the prod default. | Enforce in prod; `CSP_REPORT_ONLY` opt-in for staging |

## Verified Frontend Constraints (evidence)

| Finding | Evidence | Consequence for CSP |
|---------|----------|--------------------|
| Inline `<script>` blocks (no `src`) | 41 blocks; e.g. `templates/includes/base/scripts.html:8`, `templates/includes/dashboard/footer.html:41` (`document.write(new Date().getFullYear())`), plus create/update page scripts | `script-src` MUST include `'unsafe-inline'` |
| Inline `<style>` blocks | e.g. `templates/includes/base/head.html:15` (commented `@import rsms.me` is inactive), plus page templates | `style-src` MUST include `'unsafe-inline'` |
| External `<img>` from CDN | `static/dist/js/meteogram.js:128` and `:255` → `https://cdn.jsdelivr.net/gh/nrkno/yr-weather-symbols@8.0.1/dist/svg/...` | `img-src` MUST include `https://cdn.jsdelivr.net` |
| WRF model images | `static/dist/js/maps.js:85-86` rewrites `http://imgwrfserver.cmw.insmet.cu` → same-origin `/proxy_image_modelo/` | `img-src 'self'` suffices; no external host needed |
| `eval` / `new Function` / `setTimeout(string)` | none found in `static/dist/js` | no `'unsafe-eval'` needed |
| Web Workers / `importScripts` | none found | no `worker-src`/`child-src` needed |
| `<iframe>` in main templates | none found (emails/PDF excluded) | `frame-ancestors 'self'` covers clickjacking; no `frame-src` needed |
| `connect-src` needs | API calls (`map_station.js`, forecast) are same-origin; amCharts local | `'self'` |
| Email/PDF templates | `*/emails/`, `*/pdf.html`, `invoice/template.html` render in mail clients / WeasyPrint | Out of CSP scope (different rendering context) |

## Data Flow

```
Browser GET /<any page>/
        │
        ▼
Django view + TemplateResponse (Tabler layout, inline scripts/styles, meteogram)
        │
        ▼
ContentSecurityPolicyMiddleware (after session/auth middleware)
        │  sets: Content-Security-Policy: <CONTENT_SECURITY_POLICY dict>
        ▼
HTTP Response ──► browser enforces:
        - scripts: only 'self' + inline (unsafe-inline)
        - styles:  only 'self' + inline (unsafe-inline)
        - images:  'self', data:, https://cdn.jsdelivr.net
        - connect: 'self'
        - fonts:   'self'
        - frames/objects: blocked (frame-ancestors 'self', object-src 'none')
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `requirements.txt` | Modify | Add `django-csp>=4.0,<5.0`. |
| `config/settings.py` | Modify | Insert `csp.middleware.ContentSecurityPolicyMiddleware` into `MIDDLEWARE`. Add `CONTENT_SECURITY_POLICY` dict (see spec REQ-2) with file:line justifications as comments. Optionally add `CSP_REPORT_ONLY = env.bool('CSP_REPORT_ONLY', False)`. |
| `apps/<app>/tests/` (new test module, e.g. `apps/core/tests/test_csp.py`) | New | Assert header presence + key directives (see Testing Strategy). |
| `static/dist/js/meteogram.js` | Unchanged | Allowed via `img-src ... https://cdn.jsdelivr.net`. |
| `static/dist/js/maps.js` | Unchanged | Same-origin proxy; `img-src 'self'`. |
| `templates/**` | Unchanged | Inline code allowed via `'unsafe-inline'`. |

## Interfaces / Contracts

`CONTENT_SECURITY_POLICY` (final enforced policy):

```python
CONTENT_SECURITY_POLICY = {
    "default-src": "'self'",
    "base-uri": "'self'",
    "frame-ancestors": "'self'",
    "object-src": "'none'",
    # 'unsafe-inline' required: 41 inline <script> blocks
    # (e.g. templates/includes/base/scripts.html:8,
    #  templates/includes/dashboard/footer.html:41).
    # Nonce migration is a tracked follow-up.
    "script-src": "'self' 'unsafe-inline'",
    # 'unsafe-inline' required: inline <style> blocks
    # (e.g. templates/includes/base/head.html:15).
    "style-src": "'self' 'unsafe-inline'",
    # jsdelivr required for meteogram.js:128,255 weather-symbol SVGs.
    "img-src": "'self' data: https://cdn.jsdelivr.net",
    "font-src": "'self'",
    "connect-src": "'self'",
}
```

Emitted header example:

```
Content-Security-Policy: default-src 'self'; base-uri 'self'; frame-ancestors 'self'; object-src 'none'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https://cdn.jsdelivr.net; font-src 'self'; connect-src 'self'
```

## Testing Strategy

Repo uses `strict_tdd`; tests live in `apps/<app>/tests/`. Use Django
`TestCase` + `Client` (or `APITestCase` for an API view).

| Layer | What to Test | Approach |
|-------|--------------|----------|
| Settings | `CONTENT_SECURITY_POLICY` is a dict and contains `default-src` == `"'self'"` | Assert against `django.conf.settings.CONTENT_SECURITY_POLICY`. |
| Middleware/Header | A representative HTML page response carries `Content-Security-Policy` | `GET /` (or a page requiring auth via forced login); assert `'Content-Security-Policy' in response.headers`. |
| Directive content | Header contains `default-src 'self'`, `script-src 'self' 'unsafe-inline'`, `img-src ... https://cdn.jsdelivr.net`, `object-src 'none'` | Parse/assert substring presence. |
| Functional regression | `meteogram.js` symbols still load (jsdelivr allowed) and `/proxy_image_modelo/` WRF images still load (`'self'`) | Optional: render a page that includes meteogram; assert no CSP-block reported (staging report-only log). |

## Threat Matrix

This change adds a **defensive response header**; it introduces no new
untrusted-input execution path, no new subprocess/shell/VCS boundary, and no new
routing. Residual risk: `'unsafe-inline'` in `script-src`/`style-src` preserves
the ability for an inline-injected script to run. That residual is bounded
because `default-src 'self'` still blocks scripts/styles from *external*
origins, and the inline blocks are first-party authored code. The full XSS
closure (nonces) is explicitly deferred to a follow-up change; this change
delivers immediate external-origin isolation, which is the highest-value,
lowest-risk gain.

## Migration / Rollout

No migrations, no model/URL changes. After deploy:
- `pip install -r requirements.txt` (adds `django-csp`).
- Middleware emits the header on the next request; no collectstatic needed
  (CSP is not a static asset).
- Recommended: enable `CSP_REPORT_ONLY=True` in staging for one cycle to confirm
  zero violations, then enforce in production.

## Rollback

`git checkout -- requirements.txt config/settings.py` and reinstall deps if the
package was added. No migrations or static regeneration required. If a proxy
caches responses, purge the affected paths.

## Open Questions

- Should `CSP_REPORT_ONLY` be wired to an env var (`environ`/`env`)? Recommend
  `env.bool('CSP_REPORT_ONLY', False)` if `env` is already a dependency; else a
  plain `settings` flag. Confirm during implementation which env helper the
  project uses.
- Future: schedule the nonce-refactor follow-up change to remove
  `'unsafe-inline'`.
