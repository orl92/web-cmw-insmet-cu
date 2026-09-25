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

- [x] 1.1 `apps/home/urls.py`: `''` → `LandingView.as_view(), name='landing'`; `IndexView` → `'home/'`, `name='index'` kept; other home URLs untouched
- [x] 1.2 `apps/home/views/landing/views.py`: `LandingView(TemplateView)`; context `title='Inicio'`, `parent=''`, `segment='landing'`, `latest_forecast` (prefetch regions, None-safe), `active_warnings` (`valid_until__gte=now`, `[:3]`), `featured_services` (`record_active=True`, `-date`, `[:3]`), `og_url`
- [x] 1.3 `templates/layouts/landing.html`: extends `base.html`, blanked `html_attrs`, sticky navbar, hero outside `container-xl`, reuses home navbar/footer includes
- [x] 1.3b Rediseño estilo marketing (plan aprobado): `landing-hero` con badge + h1 display + CTAs + hero card de temperatura; secciones espaciadas (avisos, regiones, servicios, features, logos, CTA final)
- [x] 1.4 `apps/home/templates/pages/home/landing.html` (REDESIGN aprobado): hero\(latest_forecast + CTA `home:weather_today` + badge + card temp Interior, mañana\), franja avisos activos, 3 region cards (`forecast_region_card.html`), servicios destacados grid, grilla features (`ti-atom`/`ti-satellite`/`ti-book`), franja institucional CITMA/AMA/INSMET, CTA final

## Phase 2: Socials Footer & Head

- [x] 2.1 `templates/includes/base/head.html`: link `dist/css/tabler-socials.min.css?v=151` after tabler-icons (vendored, no CDN)
- [x] 2.1b `templates/includes/base/head.html`: link `dist/css/tabler-marketing.min.css?v=151` (vendored en `static/dist/css/`, NO CDN)
- [x] 2.2 `templates/includes/home/footer.html`: 4 anchors `social social-app-{facebook,instagram,x,telegram} social-gray` + `aria-label`; keep `home:index` copyright link
- [x] 2.3 `templates/includes/dashboard/footer.html`: same 4 anchors wrapped in `<li class="list-inline-item">`
- [x] 2.4 `static/dist/css/theme.css` (only if dark `social-gray` contrast < 3:1): `[data-bs-theme="dark"] .social-gray { filter: brightness(1.5); }` — NO APLICA: contraste medido 3.34:1 (≥3:1, WCAG 1.4.11) sobre `#1f2937`; no se modifica `theme.css`

## Phase 3: Landing Navbar (propio, separado del home)

- [x] 3.1 `templates/includes/landing/navbar.html` (NUEVO): navbar marketing — simple, transparente sobre hero, logo → `/`, links a páginas del sitio (`home:weather_today`, `home:models_maps`, `home:satellite`, `home:services_public`, `home:publications`), CTA `home:index` "Explorar" o `user_auth:login`; SIN menú usuario ni toggles de app
- [x] 3.2 `templates/layouts/landing.html`: usa `includes/landing/navbar.html` en el bloque navbar, NO `includes/home/navbar.html`
- [x] 3.3 (por rediseño aprobado) home navbar/menu NO llevan condicional — revierten a `{% url 'home:index' %}` siempre; la separación la da el navbar landing propio

## Phase 4: SEO/OG

- [x] 4.1 `landing.html` `{% block extrahead %}`: meta description + OG tags `og:title/description/type/url/locale` using `og_url` context; site-wide CSP unchanged (D6)

## Phase 5: Tests (RED-first, new `apps/home/tests/test_landing.py`, full labels)

- [x] 5.1 `LandingRoutingTests`: `reverse('home:landing') == '/'`, `reverse('home:index') == '/home/'`, `GET /` 200 + `assertTemplateUsed`, `home:weather_today` unchanged
- [x] 5.2 `LandingRenderTests`: with Forecasts + 9 regions + active Warning + published Services — 3 regions, hero temp, warning title, service title, links, logos present
- [x] 5.3 `LandingEmptyStateTests`: no data → `GET /` 200, no section error
- [x] 5.4 `LandingNavbarTests`: landing navbar es el propio (`includes/landing/navbar.html`) con logo → `/` y links a páginas; navbar de home (`/home/`) usa `home:index` sin condicional
- [x] 5.5 `LandingSeoTests`: meta description + 5 OG tags; CSP header present
- [x] 5.6 `LandingFooterSocialTests`: 4 `social-gray` anchors + `aria-label` (public + dashboard footer), `<html lang="es" data-bs-theme="light">`, head links socials css
- [x] 5.7 CDN scan of `apps/home/templates/pages/home/landing.html` (read-only) + `templates/layouts/landing.html` (read-only) for `cdn.jsdelivr.net`/`unpkg.com`

## Phase 6: Verification & Cleanup

- [x] 6.1 `python manage.py check` + `python manage.py test apps.home apps.core` green
- [x] 6.2 `djlint . --reformat --check` + `djlint . --lint` on touched templates (2-space indent)
- [x] 6.3 Re-run `collectstatic --link --no-input`; smoke `GET /` and `/home/` → 200

## Phase 7: Rediseño v2 — landing "muestra de producto" + ajustes globales (aprobado por maintainer)

> Feedback del maintainer: el landing NO debe repetir el contenido del home. Debe ser una muestra visual del producto, como los ejemplos Tabler marketing (tabler.io/admin-template): secciones claramente divididas con formas/imágenes que se mueven, mockups de navegador, gradientes. El contenido real (avisos, regiones, servicios) vive en el home. Además: navbar del landing debe enlazar al portal administrativo y al login; el logo apunta SIEMPRE al landing (landing, home y dashboard); el home usa el footer chico del dashboard (el grande queda solo para el landing); iconos sociales más chicos en dashboard y home.

- [x] 7.1 `apps/home/templates/pages/home/landing.html` (v2 PRODUCT SHOWCASE): reemplazar las secciones que duplican contenido del home por una vitrina visual estilo Tabler marketing:
  - Hero con badge + título + CTAs + mockup de navegador (clases `.browser`, `.browser-header`, `.browser-dots`/`.browser-dots-colored`, `.browser-input`) mostrando una UI simulada del portal con weather icons PNG (`static/dist/img/weather_icon/`) e imagen satélite GOES16 existente.
  - Secciones con alternancia de fondo (`.body-gradient`, `.body-marketing`, `.section-light`, `.section-sm`, `.section-title`, `.section-description`) claramente divididas por `border-top`/espaciado generoso.
  - Cada sección muestra UNA capacidad del producto (tiempo, avisos, modelos, satélites, servicios, publicaciones) con icono grande `ti-*`, breve descripción y CTA al home (`home:weather_today`, `home:satellite`, `home:models_maps`, `home:services_public`, `home:publications`), NO listando contenido de la BD salvo donde el hero lo requiera.
  - Franja de logos institucionales (CITMA/AMA/INSMET) y CTA final.
  - Mantener `{% block extrahead %}` SEO/OG (4.1) intacto.
- [x] 7.2 `templates/includes/landing/navbar.html` (v2): enlaces del navbar enfocados al portal: logo → `home:landing`; links a páginas clave (`home:weather_today`, `home:models_maps`, `home:satellite`); CTA "Portal" → `home:index` (portal administrativo) y "Iniciar sesión" → `user_auth:login` cuando `request.user.is_authenticated` sea falso; cuando está autenticado mostrar link simple al dashboard (`home:index`) sin menú de usuario.
- [x] 7.3 Logo global → landing: `templates/includes/home/navbar.html` y `templates/includes/dashboard/sidebar.html` cambian el href del brand de `home:index` a `home:landing` (el logo apunta SIEMPRE al landing; el item "Inicio" del menú sigue a `home:index`).
- [x] 7.4 Footer home = footer dashboard: `templates/layouts/home.html` incluye `includes/dashboard/footer.html` (chico, transparente) en lugar de `includes/home/footer.html`; el footer grande (`includes/home/footer.html`) queda SOLO en `templates/layouts/landing.html`. Verificar bloque/slots del layout home para no duplicar.
- [x] 7.5 Social icons más chicos en dashboard y home: en `templates/includes/dashboard/footer.html` (y home ahora usando ese mismo footer) los 4 anchors `social social-app-* social-gray` se renderizan más pequeños — opción preferida: envolver con clase de tamaño (verificar si Tabler soporta tamaño vía contexto; si no, CSS mínimo en `static/dist/css/theme.css`, NUNCA editar `.min.css` vendoreado). No aplicar a socials del footer landing grande.
- [x] 7.6 Tests v2 en `apps/home/tests/test_landing.py`:
  - `LandingRenderTests`: reemplazar asserts de región cards/temp hero por asserts de vitrina v2 (mockup browser presente, sección features con iconos, logos institucionales, CTA al home); hero temp solo si se decide mostrarla.
  - `LandingNavbarTests`: assert portal CTA `home:index` y `user_auth:login` (anónimo) presentes en `GET /`; logo → `/` en landing, home y dashboard (login requerido para dashboard); item "Inicio" del home → `home:index`.
  - Nuevo `LandingFooterLayoutTests`: `GET /home/` usa footer dashboard (clase `footer footer-transparent` y `<li>` socials), `GET /` usa footer grande (`includes/home/footer.html`, clase `footer` sin transparent); socials más chicos en dashboard/home.
  - Mantener/ajustar `LandingSeoTests`, `LandingEmptyStateTests`, `LandingRoutingTests` sin romper 4.1.
- [x] 7.7 Verificación final: `manage.py check` + `python manage.py test apps.home apps.core`; `djlint . --lint` + `--reformat --check` sobre archivos tocados; `collectstatic --link --no-input`; smoke `GET /` y `GET /home/` → 200 con markers de v2 presentes.

## Phase 8: Traducción completa + contenido real + páginas institucionales + fix logout (v3)

> Feedback del maintainer (2026-09-24/25): traducir al español el inglés restante de la landing, completar las secciones sin contenido real (manteniendo el aspecto), crear las páginas Visión/Misión/Quiénes Somos del navbar y actualizar los tests a coincidir con el estado en disco. El disco del usuario es la fuente de verdad.

- [ ] 8.1 `apps/home/templates/pages/home/landing.html` (v3): traducción completa — hero CTAs ("Explorar el portal" → `home:index`, "Conozca el centro" → `home:institution_about`), franja "Respaldo institucional", marketing real ("Servicios y herramientas del Centro" / "Atención especializada al cliente" / "Información oficial del INSMET" / "Vigilancia permanente del tiempo" + imagen GOES-16), stats reales (3 regiones / 13 municipios / 24/7 / 100% cobertura), newsletter ("Suscríbase al boletín del Centro"). Bugs corregidos: `</p>` sin cerrar, `http://127.0.0.1:8000/home/` hardcodeada → `{% url 'home:index' %}`, `srcset` con `preview_light@2x.png` inexistente eliminado, `title` en inglés → español, `alt` del mockup en español.
- [ ] 8.2 Páginas institucionales: `apps/home/views/institucion/institucional/views.py` (3 TemplateView con context `title`/`parent='institucion'`/`segment`), templates `pages/home/institution/{vision,mission,about}.html` (extienden `layouts/home.html`, contenido real del centro), 3 paths en `apps/home/urls.py` (`institucion/vision/`, `institucion/mision/`, `institucion/quienes-somos/`).
- [ ] 8.3 `templates/includes/landing/navbar.html` (v3): links Visión/Misión/Quiénes Somos → URLs reales (antes `#`), etiquetas con acentos correctos; se conservan brand → landing, theme toggles y bloque auth (Registrarse/Iniciar sesión / Inicio).
- [x] 8.4 Endurecimiento auth (bloqueante detectado por el hook pre-commit; commit `fix(auth)`): `config/settings.py` — `LOGOUT_REDIRECT_URL = reverse_lazy('home:index')` (antes `'/'`, que con el routing v2 cae en la landing), migración `STATICFILES_STORAGE` → `STORAGES` (WhiteNoise manifest prod / StaticFilesStorage dev), `LOGIN_URL` y `LOGIN_REDIRECT_URL` con `reverse_lazy`. `apps/user_auth/views/login.py` — logout POST-only (`HttpResponseNotAllowed(['POST'])` en GET), `_safe_next_url` con `url_has_allowed_host_and_scheme` (open-redirect), orden log→logout→mensaje (logout muta `request.user`, el log debe ir antes), constantes `ActivityLog.ACTIVITY_LOGIN/ACTIVITY_LOGOUT`. `apps/user_auth/views/users.py` — guarda anti-escalación: `get_form()` quita `is_staff`/`is_superuser` para no-superusuario (+ template); `transaction.atomic()` en `UserCreateView`; `IntegrityError` → `form_invalid` en `CustomerRegisterView`; `login(..., backend='django.contrib.auth.backends.ModelBackend')` (con LDAP multi-backend, Django 5.2 lanza ValueError → 500); `objects=self.object_list`; `extra_tags='success'`. Templates: logout de `navbar.html` (home/dashboard) y `sidebar.html` como `<form method="post">` con `{% csrf_token %}`. Tests: `test_login.py` (POST + `test_logout_rejects_get` 405), `test_views.py` (anti-escalación, multi-backend con fake form).
- [ ] 8.5 Tests v3 en `apps/home/tests/test_landing.py`: hero (CTAs traducidos, mockup `preview_light.png`, sin `127.0.0.1` ni `@2x`), capabilities con headings reales, marketing copy real (asserts positivos y negativos contra copy viejo), stats reales, newsletter, navbar institucional + toggles + auth, nuevo `InstitutionPagesTests` (URLs/templates/context).
- [ ] 8.6 Verificación final v3: `python manage.py check` + `python manage.py test apps.home apps.user_auth apps.core` green; `djlint` sobre templates tocados; smoke `GET /`, `GET /home/` y las 3 URLs institucionales → 200.