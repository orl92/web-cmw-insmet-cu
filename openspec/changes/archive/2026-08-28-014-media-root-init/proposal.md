# Proposal: Move MEDIA_ROOT Directory Creation Out of Settings Import

## Intent

`config/settings.py:280-282` creates `media/` as a side effect of importing
settings:

```python
MEDIA_ROOT = BASE_DIR / 'media'
if not MEDIA_ROOT.exists():
    MEDIA_ROOT.mkdir(parents=True)
```

This executes at module-import time, not at request time. Importing settings
happens on every management command, test bootstrap, shell, and app-registry
load, so the directory is silently created on disk as a mere consequence of
importing a module. It is also a minor anti-pattern: a filesystem side effect
during import, and it re-implements `exist_ok` with a fragile `if not exists`
branch that is racy (TOCTOU) between the check and the `mkdir`. This change
relocates directory creation to a proper startup hook so settings import stays
pure, while preserving the behavior that `media/` exists wherever uploads land
(dev/prod).

## Scope

### In Scope
- Remove the `if not MEDIA_ROOT.exists(): MEDIA_ROOT.mkdir(...)` branch from
  `config/settings.py`.
- Create `media/` at app startup via `CoreConfig.ready()` (canonical Django
  startup hook), using `Path.mkdir(parents=True, exist_ok=True)`.
- Keep `MEDIA_ROOT = BASE_DIR / 'media'` in settings (relocating the path
  declaration is out of scope).
- Add tests confirming no import-time side effect and that directory creation
  works idempotently.

### Out of Scope
- Changing the location of `MEDIA_ROOT`.
- Changing file upload logic, `FileField`/`ImageField` handling, or the storage
  backend.
- Changing the test runner (`config/test_runner.py`) or its temp MEDIA_ROOT
  behavior.

## Capabilities

### New Capabilities
- `media-root-init`: `media/` is created deterministically at application
  startup (not at settings import) using an idempotent `exist_ok` mkdir, while
  `MEDIA_ROOT` (the path value) remains declared in settings.

### Modified Capabilities
- None.

## Approach

1. In `config/settings.py` delete lines 281-282 (the `if not exists / mkdir`
   branch). Keep `MEDIA_ROOT = BASE_DIR / 'media'` (line 280) — moving the path
   declaration is out of scope.
2. In `apps/core/apps.py`, implement `CoreConfig.ready()` to ensure the
   directory exists:

   ```python
   from pathlib import Path
   from django.conf import settings

   def ready(self):
       Path(settings.MEDIA_ROOT).mkdir(parents=True, exist_ok=True)
   ```

   - **Why `AppConfig.ready()`** over a settings-import branch: it is the
     canonical Django hook for startup side effects and runs once after the app
     registry is populated (settings fully loaded), keeping settings import
     pure. It also self-heals on every `runserver`/`gunicorn` boot.
   - **Why `exist_ok=True`**: idempotent and removes the race between the
     `exists()` check and `mkdir()` (TOCTOU); a second boot never raises.
   - A management command (`ensure_media_root`) was considered as an
     alternative for explicit deploy-time invocation. It is noted in design as
     optional, but `ready()` covers dev + prod with zero extra wiring.
3. The test runner (`config/test_runner.py`, `IsolatedMediaRunner`) already
   swaps `settings.MEDIA_ROOT` to a temp dir before tests write and restores it
   after; it is unaffected. `ready()` will mkdir the real `media/` at bootstrap
   (the same as today's import-time mkdir), so there is no test regression.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `config/settings.py` | Modified | Remove import-time `if not exists / mkdir` branch (lines 281-282). |
| `apps/core/apps.py` | Modified | `CoreConfig.ready()` creates `media/` via idempotent mkdir. |
| `config/test_runner.py` | Unchanged | Still owns its temp MEDIA_ROOT. |
| `openspec/changes/014-media-root-init/specs/014-media-root-init/spec.md` | New | Delta spec. |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| `ready()` runs before `IsolatedMediaRunner` swaps MEDIA_ROOT, leaving an empty `media/` after tests | Low | Pre-existing behavior (today's import-time mkdir does the same); `media/` is gitignored. Harmless. |
| `apps.core` not in `INSTALLED_APPS` or loaded too late | Very Low | `core` is a foundational app; any always-loaded app can host the hook if needed. |
| Deploy forgets to create `media/` | Low | `ready()` runs on every `runserver`/`gunicorn` boot, so prod startup self-heals. |

## Rollback Plan

`git checkout -- config/settings.py apps/core/apps.py` (no migrations). The
import-time branch returns and creates `media/` as before.

## Dependencies

None (stdlib `pathlib` + Django settings).

## Success Criteria

- [ ] `config/settings.py` no longer creates `media/` at import time.
- [ ] `CoreConfig.ready()` creates `media/` idempotently at startup (dev/prod).
- [ ] `python manage.py test` (full suite) still passes.
- [ ] `python manage.py check` reports no errors.
