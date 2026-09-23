# Tasks: Landing Page Pública

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 500-650 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 (socials footer) → PR 2 (landing + routing + navbar + SEO + tests); optional PR 3 (navbar/SEO) if PR 2 > 400 |
| Delivery strategy | ask-on-risk |
| Chain strategy | stacked-to-main |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|---|---|---|---|---|---|
| 1 | Activate socials: `social-gray` footers (public + dashboard) + head link + footer tests | PR 1 | `python manage.py test apps.home.tests.test_landing.LandingFooterSocialTests apps.core` | runserver smoke: `/` + dashboard footer (login required) | Revert `head.html` + both footers; `btn btn-icon` icons return, no unrelated file touched |
| 2 | Landing at root: routing, `LandingView`, `landing.html`, `layouts/landing.html`, navbar conditional, SEO/OG, remaining tests | PR 2 | `python manage.py test apps.home` | runserver: `curl -s localhost:8000/` shows hero + region cards | Revert `urls.py` + delete view/templates; `/` returns to `IndexView` |

## Phase 1: Routing & Landing Infrastructure

- [ ] 1.1 `apps/home/urls.py`: `''` → `LandingView.as_view(), name='landing'`; `IndexView` → `'home/'`, `name='index'` kept; other home URLs untouched
- [ ] 1.2 `apps/home/views/landing/views.py`: `LandingView(TemplateView)`; context `title='Inicio'`, `parent=''`, `segment='landing'`, `latest_forecast` (prefetch regions, None-safe), `active_warnings` (`valid_until__gte=now`, `[:3]`), `featured_services` (`record_active=True`, `-date`, `[:3]`), `og_url`
- [ ] 1.3 `templates/layouts/landing.html`: extends `base.html`, blanked `html_attrs`, sticky navbar, hero outside `container-xl`, reuses home navbar/footer includes
- [ ] 1.4 `apps/home/templates/pages/home/landing.html`: hero (latest_forecast + CTA `home:weather_today`), warnings strip, 3 region cards (`forecast_region_card.html`), featured services, models/satellites/publications links, institution logos (CITMA/AMA/INSMET)

## Phase 2: Socials Footer & Head

- [x] 2.1 `templates/includes/base/head.html`: link `dist/css/tabler-socials.min.css?v=151` after tabler-icons (vendored, no CDN)
- [x] 2.2 `templates/includes/home/footer.html`: 4 anchors `social social-app-{facebook,instagram,x,telegram} social-gray` + `aria-label`; keep `home:index` copyright link
- [x] 2.3 `templates/includes/dashboard/footer.html`: same 4 anchors wrapped in `<li class="list-inline-item">`
- [ ] 2.4 `static/dist/css/theme.css` (only if dark `social-gray` contrast < 3:1): `[data-bs-theme="dark"] .social-gray { filter: brightness(1.5); }`

## Phase 3: Conditional Navbar

- [ ] 3.1 `templates/includes/home/navbar.html`: brand href `'/'` when `request.resolver_match.url_name == 'landing'` (None-safe guard), else `{% url 'home:index' %}`
- [ ] 3.2 `templates/includes/home/menu-list.html`: "Inicio" item uses the same conditional href

## Phase 4: SEO/OG

- [ ] 4.1 `landing.html` `{% block extrahead %}`: meta description + OG tags `og:title/description/type/url/locale` using `og_url` context; site-wide CSP unchanged (D6)

## Phase 5: Tests (RED-first, new `apps/home/tests/test_landing.py`, full labels)

- [ ] 5.1 `LandingRoutingTests`: `reverse('home:landing') == '/'`, `reverse('home:index') == '/home/'`, `GET /` 200 + `assertTemplateUsed`, `home:weather_today` unchanged
- [ ] 5.2 `LandingRenderTests`: with Forecasts + 9 regions + active Warning + published Services — 3 regions, hero temp, warning title, service title, links, logos present
- [ ] 5.3 `LandingEmptyStateTests`: no data → `GET /` 200, no section error
- [ ] 5.4 `LandingNavbarConditionalTests`: on landing brand+"Inicio" href `/`; on `/home/` both `/home/`
- [ ] 5.5 `LandingSeoTests`: meta description + 5 OG tags; CSP header present
- [x] 5.6 `LandingFooterSocialTests`: 4 `social-gray` anchors + `aria-label` (public + dashboard footer), `<html lang="es" data-bs-theme="light">`, head links socials css
- [ ] 5.7 CDN scan of `apps/home/templates/pages/home/landing.html` (read-only) + `templates/layouts/landing.html` (read-only) for `cdn.jsdelivr.net`/`unpkg.com`

## Phase 6: Verification & Cleanup

- [ ] 6.1 `python manage.py check` + `python manage.py test apps.home apps.core` green
- [ ] 6.2 `djlint . --reformat --check` + `djlint . --lint` on touched templates (2-space indent)
- [ ] 6.3 Re-run `collectstatic --link --no-input`; smoke `GET /` and `/home/` → 200