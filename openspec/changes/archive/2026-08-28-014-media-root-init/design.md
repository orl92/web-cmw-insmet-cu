# Design: Move MEDIA_ROOT Directory Creation Out of Settings Import

## Technical Approach

Keep the `MEDIA_ROOT` path declaration in `config/settings.py` but remove the
import-time filesystem side effect (the `if not MEDIA_ROOT.exists():
MEDIA_ROOT.mkdir(parents=True)` block). Move directory creation to
`CoreConfig.ready()` (the Django app-startup hook), using
`Path(settings.MEDIA_ROOT).mkdir(parents=True, exist_ok=True)`. This makes
directory creation deterministic and idempotent, and removes the import-time
side effect entirely. `ready()` runs once after the app registry is populated
(settings fully configured), so `settings.MEDIA_ROOT` is safely available.

## Architecture Decisions

| Decision | Options | Tradeoff | Chosen |
|----------|---------|----------|--------|
| Where to create `media/` | (a) `AppConfig.ready()` vs (b) management command vs (c) settings-import `exist_ok` | (a) self-heals on every boot (dev+prod), zero extra wiring, keeps import pure. (b) explicit but requires wiring into deploy/startup and can be forgotten. (c) keeps an import-time side effect (fails REQ-1). | (a) `CoreConfig.ready()` |
| Idempotency | `if not exists: mkdir` vs `mkdir(exist_ok=True)` | `exist_ok=True` removes the TOCTOU race and a second boot never raises. | `exist_ok=True` |
| Move `MEDIA_ROOT` path declaration | yes vs no | Out of scope per change brief; declaration stays in settings. | keep in settings |

## Data Flow

```
Django boots → apps populate → CoreConfig.ready()
        │
        ▼
Path(settings.MEDIA_ROOT).mkdir(parents=True, exist_ok=True)
        │
        ▼
media/ exists on disk (idempotent; no-op if already present)

Tests: IsolatedMediaRunner.setup_test_environment()
        │  settings.MEDIA_ROOT → temp dir
        ▼
uploads go to temp; real media/ (if created at boot) is untouched & gitignored
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `config/settings.py` | Modify | Delete the `if not MEDIA_ROOT.exists(): MEDIA_ROOT.mkdir(parents=True)` branch (lines 281-282). Keep `MEDIA_ROOT = BASE_DIR / 'media'`. |
| `apps/core/apps.py` | Modify | Implement `CoreConfig.ready()` to call `Path(settings.MEDIA_ROOT).mkdir(parents=True, exist_ok=True)`. Reference `settings` inside the method to avoid module-import settings access. |
| `openspec/changes/014-media-root-init/specs/014-media-root-init/spec.md` | New | Delta spec. |

## Interfaces / Contracts

No external interface change. `MEDIA_ROOT` (the path value) is unchanged.
Behavior contract: after app startup, `MEDIA_ROOT` exists on disk with
`exist_ok` semantics.

## Testing Strategy

Repo uses `strict_tdd`; tests live in `apps/core/tests/`. Three layers:

| Layer | What to Test | Approach |
|-------|--------------|----------|
| Static | `config/settings.py` no longer contains the import-time mkdir branch | Read the source and assert `'MEDIA_ROOT.mkdir'` is absent (or the `if not MEDIA_ROOT.exists()` branch is gone). Guards REQ-1. |
| Unit | `CoreConfig.ready()` creates a missing directory | Monkeypatch `settings.MEDIA_ROOT` to a fresh `tmp_path`; call `apps.core.apps.CoreConfig(...).ready()`; assert the dir exists. Guards REQ-2. |
| Unit | Idempotency | Call the mkdir logic twice on the same `tmp_path`; assert no exception and the dir still exists (simulates `exist_ok`). |
| Integration | Full suite unaffected | `python manage.py test` — `IsolatedMediaRunner` still owns its temp MEDIA_ROOT. Guards REQ-3. |

Note: the static test is intentionally a source-level assertion because REQ-1
is a "no side effect at import" guarantee that cannot be observed after the
fact once the directory may already exist on disk.

## Threat Matrix

`N/A — no routing, shell, subprocess, VCS/PR automation, executable-file
classification, or process-integration boundary is changed.` This is a
filesystem-directory creation at startup; no untrusted input is executed and
the directory is created under the already-declared `MEDIA_ROOT` path.

## Migration / Rollout

No migrations, no model/URL/settings-value changes. After merge, the next
`runserver`/`gunicorn` boot self-creates `media/` via `ready()`. `media/` is
already gitignored.

## Rollback

`git checkout -- config/settings.py apps/core/apps.py`. Import-time branch
returns; `media/` created as before.

## Open Questions

None.
