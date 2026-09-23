# Proposal: Landing Page Pública

## Intent

`/` serves the heavy admin-facing home (`IndexView`, ~300 lines, amCharts) — slow, unfocused for visitors. The CMP portal needs a light public landing at `/`; the home moves to `/home/` without breaking `reverse('home:index')` (14 templates, 4 test suites rely on it).

## Scope

### In Scope
- `LandingView` + template + `layouts/landing.html` at `/` (`name='landing'`); `IndexView` → `/home/` (`name='index'` preserved).
- Sections: hero (`latest_forecast` + CTA), warnings strip (`menu_notifications`), 3 region cards (reuse `forecast_region_card.html`), featured services, models/satellites/publications links, institution block (CITMA/AMA/INSMET logos).
- **Footer social-gray**: 4 anchors → `social social-app-{facebook,instagram,x,telegram} social-gray` in public **and** dashboard footer; `<link tabler-socials.min.css?v=151>` in `head.html`.
- **Navbar conditional**: logo/"Inicio" → `/` only when `url_name == 'landing'`.
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