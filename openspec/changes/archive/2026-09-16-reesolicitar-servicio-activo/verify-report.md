```yaml
schema: gentle-ai.verify-result/v1
evidence_revision: sha256:055a0cc0e4497f908401aeabb64b3c8f9219d69aaac279b1064c6ba96591c440
verdict: pass
blockers: 0
critical_findings: 0
requirements: 4/4
scenarios: 7/7
test_command: python manage.py test
test_exit_code: 0
test_output_hash: sha256:ef22920b964fb7546f08f2281b7fd45587110969965c511f8dc04d546fae86d1
build_command: python manage.py check
build_exit_code: 0
build_output_hash: sha256:1e3e63f221bde88816c4a4ef7367691607b20cc1d194028a02ec9ae0586cf9b1
```

## Verification Report

**Change**: reesolicitar-servicio-activo
**Version**: spec amended 2026-09-16 (post verify FAIL `a00188fe`; maintainer-approved alignment of the spec to the real HEAD state, ledger intent `spec-enmienda-estado-real` closed passed)
**Mode**: Strict TDD (`testing.strict_tdd: true`, runner `django_unittest`)

### Completeness
| Metric | Value |
|--------|-------|
| Tasks total | 20 |
| Tasks complete | 20 |
| Tasks incomplete | 0 |

All tasks complete; full verification ran.

### Build & Tests Execution
**Build**: ✅ Passed
```text
python manage.py check
System check identified no issues (0 silenced).
exit code: 0 — output sha256: 1e3e63f221bde88816c4a4ef7367691607b20cc1d194028a02ec9ae0586cf9b1
```

**Tests (full suite, rules.verify.test_command)**: ✅ 743 passed / ❌ 0 failed / ⚠️ 0 skipped
```text
python manage.py test
Ran 743 tests in 405.766s
OK
exit code: 0 — output sha256: ef22920b964fb7546f08f2281b7fd45587110969965c511f8dc04d546fae86d1
```

**Tests (affected apps)**: ✅ 392 passed / ❌ 0 failed
```text
python manage.py test apps.commercial apps.home
Ran 392 tests in 250.769s
OK
exit code: 0 — output sha256: d11213fb4397c3e5fb46f4ce07e1595f5bd17d922f6aa43ec9e5942db23b9a39
```

**Tests (change classes)**: ✅ 17 passed / ❌ 0 failed
```text
python manage.py test apps.commercial.tests.test_views.ServiceReRequestTests apps.home.tests.test_services_ui.ServiceReRequestUiTests
Ran 17 tests in 5.734s
OK
exit code: 0 — output sha256: c26539d3d23920f8534b97aa622659216450d625fa157b1eec9192031b7669a7
```

**Lint (changed files)**: ✅ ruff clean (exit 0) · ✅ djlint 0 errors (exit 0)
```text
ruff check apps/home/views/servicios/comerciales/views.py apps/home/tests/test_services_ui.py apps/commercial/tests/test_views.py
All checks passed!
djlint --reformat --check --lint apps/home/templates/pages/home/services/service_detail.html apps/home/templates/pages/home/services/commercial_public.html
Linted 2 files, found 0 errors.
```

**Coverage**: ➖ Not available (`coverage_tool: none` in `openspec/config.yaml`) — not a failure.

### Spec Compliance Matrix

Amended spec: 4 requirements (`### Requirement:` headings) / 7 scenarios (`#### Scenario:` headings).

| Requirement | Scenario | Test | Result |
|-------------|----------|------|--------|
| REQ-01 | Re-request with active paid subscription creates new requested row | `apps/commercial/tests/test_views.py > ServiceReRequestTests.test_form_valid_with_active_paid_creates_requested_row` | ✅ COMPLIANT |
| REQ-01 | Active paid subscription renders form with active-until alert | `apps/home/tests/test_services_ui.py > ServiceReRequestUiTests.test_active_paid_renders_form_and_cta` | ✅ COMPLIANT |
| REQ-02 | Blocked when requested subscription exists | `ServiceReRequestTests.test_form_valid_blocked_with_requested_sub` | ✅ COMPLIANT |
| REQ-02 | Blocked when pending subscription exists | `ServiceReRequestTests.test_form_valid_blocked_with_pending_sub` | ✅ COMPLIANT |
| REQ-02 | Detail view hides form for in-flight subscription | `ServiceReRequestUiTests.test_in_flight_hides_form_and_button` + `test_in_flight_pending_hides_form` | ✅ COMPLIANT |
| REQ-04 | Context with only active paid subscription | `ServiceReRequestUiTests.test_active_paid_renders_form_and_cta` (behavioral: "activa hasta …" alert renders → `active_subscription` set; form renders → `in_flight_subscription` falsy) | ✅ COMPLIANT |
| REQ-06 | Feature ships without migrations | static: 0 migration files in change/worktree, model has no `UniqueConstraint`/`unique_together` on `(customer, service)`; behavioral: `test_form_valid_with_active_paid_creates_requested_row` + `test_public_list_state_neutral_regardless_of_subscription_state` create multiple rows for one pairing without DB error | ✅ COMPLIANT |

**Compliance summary**: 7/7 scenarios compliant, 4/4 requirements complete.

### Correctness (Static Evidence)
| Requirement | Status | Notes |
|------------|--------|-------|
| REQ-01 | ✅ Implemented | `form_valid` guards only on `payment_status__in=['requested','pending']` (views.py:152-156); creates `requested` row (167-175); existing `paid` row untouched; `success_url` = `commercial:suscripcion_list` (line 84) |
| REQ-02 | ✅ Implemented | in-flight guard → warning message + redirect to `ServiceDetailView` (views.py:157-161); template renders alert block without form/button for in-flight (service_detail.html:65-75) |
| REQ-04 | ✅ Implemented | `in_flight_subscription` (requested/pending latest) and `active_subscription` (paid + `end_date > now` latest) set at views.py:121-135; `existing_subscription` key fully removed (0 references) |
| REQ-06 | ✅ Implemented | no schema change; `ServiceSubscription` has no uniqueness constraint on `(customer, service)` (models.py:173+) — multiple rows coexist (renewal precedent) |

### Coherence (Design)
| Decision | Followed? | Notes |
|----------|-----------|-------|
| D1: `form_valid` blocks only `requested`/`pending` | ✅ Yes | views.py:152-156 |
| D2: split `existing_subscription` into `in_flight_subscription`/`active_subscription` | ✅ Yes | views.py:121-135; template branches on both; old key gone |
| D3: deterministic per-service `user_subscriptions` resolver (precedence in-flight > paid active) in `PublicCommercialServicesListView` | ⚠️ No | resolver absent from HEAD (views.py:73-78) — the public catalog is state-neutral. Deviation has NO spec impact after amendment: REQ-05 was removed and catalog neutrality is owned by the promoted spec `home-public-services-layout` |

### TDD Compliance
| Check | Result | Details |
|-------|--------|---------|
| TDD Evidence reported | ⚠️ Missing table | No `apply-progress` artifact with a "TDD Cycle Evidence" table exists (locator unresolved in openspec store; Engram has no such record). Already surfaced as CRITICAL in the superseded FAIL report `a00188fe`; the maintainer's remediation accepted the historical apply as-is, so this report keeps it as a non-blocking WARNING and re-verifies RED/GREEN live |
| All tasks have tests | ✅ | Test-writing tasks (3.1-3.3, 4.1-4.6) have covering tests in 2 files; view/template tasks are exercised by the same tests |
| RED confirmed (tests exist) | ✅ | 17 tests across `ServiceReRequestTests` (3) + `ServiceReRequestUiTests` (14) verified present |
| GREEN confirmed (tests pass) | ✅ | 17/17 direct class run OK; 392/392 affected-apps OK; 743/743 full suite OK |
| Triangulation adequate | ⚠️ | REQ-01/REQ-02 well triangulated (2-3 tests each); REQ-04 S1 covered behaviorally only (no direct context assertion); REQ-06 static + behavioral |
| Safety Net for modified files | ⚠️ | Historical: test/template files were later rewritten by parallel-feature commits; no per-commit safety-net evidence recorded (documented in superseded report) |

**TDD Compliance**: RED + GREEN fully verified live; evidence table missing (WARNING), triangulation and safety-net partial (⚠️).

### Test Layer Distribution
| Layer | Tests | Files | Tools |
|-------|-------|-------|-------|
| Unit (Django TestCase, client-driven) | 17 | 2 | django_unittest |
| Integration (DRF APITestCase) | — | — | not installed |
| E2E | — | — | not installed |
| **Total** | **17** | **2** | |

### Changed File Coverage
Coverage analysis skipped — no coverage tool detected (`coverage_tool: none`). Not a failure.

### Assertion Quality
| File | Line | Assertion | Issue | Severity |
|------|------|-----------|-------|----------|
| `apps/home/tests/test_services_ui.py` | 946 | `assertIn('Solicitar', html)` | Weak substring — also matches "Solicitar de nuevo"-style labels and the related-card buttons; with unified "Solicitar" it does verify the label but not that the submit button inside the form carries it | SUGGESTION |
| `apps/home/tests/test_services_ui.py` | 966, 977, 985, 995 | comments citing "REQ-06: el catálogo es neutral" / "REQ-07" | Stale comments referencing requirement numbering that matches no open spec (max spec REQ number is 06 = no schema change) | SUGGESTION |

No tautologies, no ghost loops, no type-only assertions, no smoke-only tests; every test drives production code via `client.get`/`client.post` and asserts concrete rendered/DB state.

**Assertion quality**: 0 CRITICAL, 0 WARNING, 2 SUGGESTION.

### Quality Metrics
**Linter**: ✅ No errors (ruff, exit 0) · **Template linter**: ✅ No errors (djlint, exit 0) · **Type Checker**: ➖ Not available (`type_checker: none`)

### Issues Found
**CRITICAL**: None

**WARNING**:
1. Design deviation D3 — the deterministic per-service `user_subscriptions` resolver is not present at HEAD. No spec impact after the amendment (REQ-05 removed; state-neutral catalog owned by `home-public-services-layout`). Keep as documented deviation.
2. TDD Cycle Evidence table absent from apply evidence (apply-progress unresolved; no Engram record) — process-evidence gap from the historical apply phase; downgraded from the superseded report's CRITICAL because the maintainer's remediation accepted the historical apply, and RED/GREEN are re-verified live in this run.

**SUGGESTION**:
1. Strengthen `test_active_paid_renders_form_and_cta` to assert the exact submit-button label inside `#subscription-form` (e.g. `assertIn('> Solicitar <', html)`) instead of the weak `assertIn('Solicitar', html)`.
2. Add a direct context-level assertion for REQ-04 S1 (`self.assertIsNone(ctx['in_flight_subscription'])` / `ctx['active_subscription'] == paid`) to complement the behavioral coverage.
3. Assert the success-path redirect explicitly (`assertRedirects(response, reverse('commercial:suscripcion_list'))`) in `test_form_valid_with_active_paid_creates_requested_row` (currently covered by code inspection + `FormView` contract).
4. Clean stale test comments referencing "REQ-06: catálogo neutral" / "REQ-07" that match no open spec.

### Verdict
PASS
The amended spec (4 requirements / 7 scenarios) is fully implemented at HEAD: every scenario has a passing covering test (17/17 change classes, 392/392 affected apps, 743/743 full suite), `manage.py check`, ruff and djlint are clean, and no migration accompanies the change. The two WARNINGs (design deviation D3 with zero spec impact, and the historical TDD-evidence-table gap accepted by the remediation) are non-blocking.
