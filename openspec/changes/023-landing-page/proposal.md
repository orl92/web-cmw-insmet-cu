# Proposal: Landing Page Pública

## Intent

`/` serves the heavy admin-facing home (`IndexView`, ~300 lines, amCharts) — slow, unfocused for visitors. The CMP portal needs a light public landing at `/`; the home moves to `/home/` without breaking `reverse('home:index')` (14 templates, 4 test suites rely on it).

## Scope

### In Scope
- `LandingView` + template + `layouts/landing.html` at `/` (`name='landing'`); `IndexView` → `/home/` (`name='index'` preserved).
- Sections: hero (`latest_forecast` + CTA), warnings strip (`menu_notifications`), 3 region cards (reuse `forecast_region_card.html`), featured services, models/satellites/publications links, institution block (CITMA/AMA/INSMET logos).
- **Footer social-gray**: 4 anchors → `social social-app-{facebook,instagram,x,telegram} social-gray` in public **and** dashboard footer; `<link tabler-socials.min.css?v=151>` in `head.html`.
- **Navbar conditional**: logo/"Inicio" → `/` only when `url_name == 'landing'`.
- **Auth hardening (derivado del routing v2)**: logout POST-only con redirect a `home:index`, `next` rebotado con `url_has_allowed_host_and_scheme`, orden log→logout→mensaje, guarda anti-escalación (`is_staff`/`is_superuser` solo superusuario), `login(..., backend=ModelBackend)` (multi-backend LDAP), `transaction.atomic()` + `IntegrityError` → `form_invalid`, migración `STATICFILES_STORAGE` → `STORAGES` (WhiteNoise manifest), `LOGIN_URL`/`*_REDIRECT_URL` con `reverse_lazy`.
- **SEO/OG minimum**: meta description + basic OG tags on the landing only.

### Out of Scope
- amCharts/plots on the landing; redesign of `/home/`; SEO/OG elsewhere; CSP/dark-mode theme fixes.
- `Warning` soft-delete (model has no `record_active` — documented, not fixed).

## Capabilities

### New Capabilities
- `public-landing-page`: landing at `/` (hero, warnings, region cards, services, institution block, navbar conditional, minimal SEO/OG), keeping `home:index` on `/home/`.

### Modified Capabilities
- `tabler-core-vendor`: delta — `head.html` SHALL link socials CSS; footers SHALL use `social social-app-* social-gray` (activates vendored SOCIALS-PLUGIN).

## Approach

Exploration Approach 1: `layouts/landing.html` extends `base.html`, REUSES `includes/home/navbar.html` + `footer.html` (no duplication; hero full-bleed outside `container-xl`). Conservative naming keeps `reverse('home:index')`. No model changes → no migrations.

## Affected Areas

| Area | Impact |
|---|---|
| `apps/home/urls.py` | Modified: `''`→landing, `'home/'`→index |
| `apps/home/views/landing/views.py` | New: `LandingView` |
| `apps/home/templates/pages/home/landing.html` | New: template |
| `templates/layouts/landing.html` | New: layout, full-bleed hero |
| `templates/includes/base/head.html` | Modified: link `tabler-socials.min.css?v=151` |
| `templates/includes/{home,dashboard}/footer.html` | Modified: social-gray |
| `templates/includes/home/navbar.html` | Modified: conditional href |
| `config/settings.py` | Modified: `LOGOUT_REDIRECT_URL`→`reverse_lazy('home:index')`, `STORAGES` (WhiteNoise manifest prod), `LOGIN_URL`/`LOGIN_REDIRECT_URL` con `reverse_lazy` |
| `apps/user_auth/views/login.py` | Modified: logout POST-only (405 en GET), `_safe_next_url` con `url_has_allowed_host_and_scheme`, orden log→logout→mensaje, constantes `ActivityLog` |
| `apps/user_auth/views/users.py` | Modified: guarda anti-escalación (`is_staff`/`is_superuser` solo superusuario), `transaction.atomic()`, `IntegrityError` → `form_invalid`, `login(..., backend=ModelBackend)` |
| `apps/user_auth/tests/test_login.py`, `tests/test_views.py` | Modified: tests del endurecimiento (logout POST+405, anti-escalación, multi-backend) |
| `apps/user_auth/templates/pages/user_auth/users/update.html` | Modified: switches staff/superuser solo visibles a superusuario |
| `openspec/changes/023-landing-page/tasks.md` | Modified: Fase 8 (v3, declare auth hardening) |

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Footer swap changes visuals across 15 public pages (a11y/contrast) | Med | Full CI + djlint + smoke test |
| `social-gray` contrast in dark mode | Med | Verify AA; theme.css filter if needed |
| Navbar href swap misbehaves off-landing | Low | Strict `url_name` conditional; tested |
| Landing hits CDN-reference check | Low | Keep assets vendored |

## Rollback Plan

`git revert` the change commit: `/` returns to `IndexView`, `/home/` removed, footer/head/navbar reverted. No schema impact; re-run `collectstatic`.

## Dependencies

- `tabler-socials.min.css` + `img/social/` vendored (tabler-151-upgrade).
- `menu_notifications` processor (`apps/core`).

## Success Criteria

- [ ] `GET /` → 200 + `landing.html`, `reverse('home:landing') == '/'`; `reverse('home:index') == '/home/'` → 200.
- [ ] Footers: `social social-app-* social-gray` anchors with `aria-label`; socials CSS linked in head.
- [ ] Navbar → `/` on landing, `/home/` elsewhere; SEO/OG meta in landing `<head>`.
- [ ] `python manage.py test apps.home apps.core` green; CI full suite green.