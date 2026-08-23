# Tasks: Move MEDIA_ROOT Directory Creation Out of Settings Import

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~25 (settings + apps.py + tests) |
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

- [ ] 1.1 In `config/settings.py` remove the import-time branch (lines 281-282):
  delete `if not MEDIA_ROOT.exists():` and `MEDIA_ROOT.mkdir(parents=True)`, keeping
  `MEDIA_ROOT = BASE_DIR / 'media'`.
- [ ] 1.2 In `apps/core/apps.py` implement `CoreConfig.ready()` to create the
  directory idempotently:

  ```python
  from pathlib import Path
  from django.conf import settings

  def ready(self):
      Path(settings.MEDIA_ROOT).mkdir(parents=True, exist_ok=True)
  ```

  Reference `settings` inside the method (never at module top level).

## Phase 2: Tests (strict_tdd)

- [ ] 2.1 Static test (REQ-1): read `config/settings.py` source and assert the
  import-time mkdir branch is gone (`'MEDIA_ROOT.mkdir'` not present / no
  `if not MEDIA_ROOT.exists()` block).
- [ ] 2.2 Unit test (REQ-2): monkeypatch `settings.MEDIA_ROOT` to a fresh
  `tmp_path`, instantiate `CoreConfig`, call `ready()`, and assert the directory
  now exists.
- [ ] 2.3 Unit test (REQ-2): call the mkdir logic twice on the same `tmp_path`
  and assert no exception is raised (idempotency / `exist_ok`).

## Phase 3: Verification

- [ ] 3.1 Run the full suite `python manage.py test` — `IsolatedMediaRunner`
  still manages its temp MEDIA_ROOT; all tests pass (REQ-3).
- [ ] 3.2 Run `python manage.py check` — no system check errors.

## Phase 4: Documentation

- [ ] 4.1 (Optional) Note in deploy/runbook that `media/` self-creates at
  startup via `CoreConfig.ready()`; no manual step required.

## Phase 5: Commit

- [ ] 5.1 Commit `config/settings.py` and `apps/core/apps.py` (plus tests) with
  a conventional message referencing `014-media-root-init`.
