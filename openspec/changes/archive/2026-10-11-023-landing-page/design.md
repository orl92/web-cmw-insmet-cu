# Design: Landing Page Pública

## Technical Approach

Light public landing at `/` replacing the admin home; home moves to `/home/` keeping `reverse('home:index')` stable. New `templates/layouts/landing.html` extends `base.html` and REUSES `includes/home/{navbar,footer}.html` (no duplication, identical theme/CSP head). `LandingView` (TemplateView, `apps/home/views/landing/views.py`) supplies forecast/regions, active warnings and featured services; warning counts come from the existing `menu_notifications` processor; nav state reads `request.resolver_match.url_name` via the already-registered `request` context processor — zero new plumbing. The same change activates the vendored socials plugin (head link + `social-gray` footers). No model changes → no migrations. Specs: `public-landing-page`, `tabler-core-vendor` (delta).

## Architecture Decisions

| # | Decision | Alternatives | Choice + rationale |
|---|---|---|---|
| D1 | Route swap | (a) landing takes `name='index'`; (b) `index` → `/home/`, new `landing` at `/` | (b): 14 templates + 4 suites use `home:index` — keeping the name zero-breaks; exploration Approach 1. |
| D2 | `url_name` in navbar/menu | (a) new context processor; (b) per-view var; (c) `request.resolver_match.url_name` | (c): `request` processor already enabled (settings.py:231). Guard `{% if request.resolver_match and request.resolver_match.url_name == 'landing' %}` — strict equality, None-safe. |
| D3 | LandingView data | single TemplateView vs template sub-queries | Single view, `prefetch_related('regions','extended_days')` same as IndexView; context contract below. |
| D4 | Hero full-bleed | extend `layouts/home.html` (hero trapped in `container-xl`, residual page-header) | New `layouts/landing.html`: blanked `html_attrs` (like home.html, keeps vertical navbar-position off), sticky navbar, hero outside `container-xl`, then `container-xl` sections, footer. |
| D5 | Footer swap | keep `btn btn-icon` + ti-icons | Socials plugin per spec: 4 anchors `social social-app-{facebook,instagram,x,telegram} social-gray` + `aria-label`, public AND dashboard footer; wrap dashboard anchors in `<li>` (currently invalid `<a>` under `<ul>`). |
| D6 | SEO/OG | block placement | `{% block extrahead %}` in landing page template (renders inside `<head>`): meta description + `og:title/description/type/url/locale`. `og_url` = `request.build_absolute_uri(reverse('home:landing'))` from view. |
| D7 | social-gray dark contrast | edit vendored CSS vs override | Never touch vendored assets. Measure first (`?theme=dark`); if <3:1 add `[data-bs-theme="dark"] .social-gray { filter: brightness(1.5); }` to `theme.css` (loaded after tabler). |

## Data Flow

```
GET / ──resolve──> home:landing ──> LandingView ──context──> layouts/landing.html
                                    │  latest_forecast (prefetch regions) ──> hero + forecast_region_card x3 (north/interior/south)
                                    │  active_warnings (valid_until>=now, [:3]) ──> warnings strip (link per warning_type)
                                    │  featured_services (record_active, -date, [:3]) ──> services section
                                    │  og_url ──> extrahead OG tags
                                    │  (warning counts: menu_notifications processor, shared)
                                    └── navbar: request.resolver_match.url_name=='landing' → href '/', else /home/
```

## File Changes

| File | Action | Description |
|---|---|---|
| `apps/home/urls.py` | Modify | `path('', LandingView.as_view(), name='landing')`; `IndexView` → `path('home/', ..., name='index')` |
| `apps/home/views/landing/views.py` | Create | `LandingView(TemplateView)` |
| `apps/home/templates/pages/home/landing.html` | Create | Sections: hero (latest_forecast + CTA `home:weather_today`), warnings strip, 3 region cards (`includes/home/forecast_region_card.html`, `show_sea` north/south), featured services, links (models/satellites/publications), institution logos block; `{% block extrahead %}` SEO/OG |
| `templates/layouts/landing.html` | Create | Extends `base.html`; reuses navbar/footer includes; full-bleed hero |
| `templates/includes/base/head.html` | Modify | `<link href="{% static '' %}dist/css/tabler-socials.min.css?v=151" rel="stylesheet" />` after tabler-icons |
| `templates/includes/home/footer.html` | Modify | 4 social-gray anchors (same URLs, `aria-label`); copyright link stays `home:index` |
| `templates/includes/dashboard/footer.html` | Modify | Same 4 anchors in `<li class="list-inline-item">` |
| `templates/includes/home/navbar.html` + `menu-list.html` | Modify | Conditional `href`: `'/'` on landing else `{% url 'home:index' %}` (brand in navbar.html; "Inicio" item in menu-list.html) |
| `apps/home/tests/test_landing.py` | Create | See Testing |
| `static/dist/css/theme.css` | Modify | Only if dark contrast <3:1 (D7) |

## Interfaces / Contracts

`LandingView` context: `title='Inicio'`, `parent=''`, `segment='landing'`, `latest_forecast` (None-safe, same as IndexView), `active_warnings` (`Warning.objects.filter(valid_until__gte=now).select_related('user').order_by('-date')[:3]`), `featured_services` (`Service.objects.filter(record_active=True).select_related('user').order_by('-date')[:3]`), `og_url`.

## CSS / JS

Reused: `tabler.min.css`, `tabler-themes`, `tabler-icons`, `theme.css`, `tabler.min.js`, `tabler-theme.min.js`, weather-icon PNGs (via `get_img_path`), `forecast.css` NOT pulled (region card needs no custom CSS). Added: socials stylesheet link only; optional dark `filter` in `theme.css`; zero new JS, zero CDN.

## Testing Strategy

`apps/home/tests/test_landing.py` (Django TestCase, full labels):

| Class | Asserts |
|---|---|
| `LandingRoutingTests` | `reverse('home:landing')=='/'` + `GET /` 200 `assertTemplateUsed landing.html`; `reverse('home:index')=='/home/'` 200 + index.html; spot-check another URL (`home:weather_today`) unchanged |
| `LandingRenderTests` (creates Forecasts + 9 ForecastRegions, Warning valid, published Services) | Sections present: 3 region names, hero temp, warning `title`, service `title`, links to models/satellite/publications, CITMA/AMA/INSMET logos |
| `LandingEmptyStateTests` | No data → `GET /` 200, no section error |
| `LandingNavbarConditionalTests` | On landing brand+"Inicio" href `/`; on `/home/` both `/home/` |
| `LandingSeoTests` | meta description + 5 OG tags present; CSP header present |
| `LandingFooterSocialTests` | 4 `social social-app-* social-gray` anchors with `aria-label` on public footer (landing) and dashboard footer; `<html lang="es" data-bs-theme="light">`; head links socials css |

Suites: `python manage.py test apps.home apps.core`; CI full (templates/static touched). Add no-CDN assertion for the 2 new templates (`cdn.jsdelivr.net`/`unpkg.com` scan — existing scan only walks `templates/`). djlint both new templates.

## Threat Matrix

Routing here is Django URLconf application routing, not a shell/subprocess/VCS/PR boundary. All rows `N/A` (documentation-like paths, git selection, commit, push, PR commands) — no RED tests required.

## Migration / Rollout

None — no schema. Rollback: `git revert` + `collectstatic`. Estimate ~500-550 changed lines: `sdd-tasks` must forecast the 400-line budget under `ask-on-risk` (footer swap is the clean chained-PR slice).

## Open Questions

- [ ] Featured services: exactly 3 most recent (type-agnostic) — confirm slice at tasks.
- [ ] Title branding: keep `title='Inicio'` on the landing (nav item semantics) — SEO title can be tuned later.
