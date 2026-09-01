# media-root-init Specification

## Purpose

Ensure the `media/` upload directory exists on disk for dev/prod without
performing filesystem side effects at settings import time. The directory is
created deterministically and idempotently at application startup
(`CoreConfig.ready()`), while `MEDIA_ROOT` (the path) remains declared in
settings. The test suite's `IsolatedMediaRunner` keeps managing its own
temporary MEDIA_ROOT and is unaffected.

## Requirements

### Requirement: REQ-1 — No Import-Time Side Effect

`config/settings.py` MUST NOT create the filesystem directory as a side effect
of importing settings. The `MEDIA_ROOT = BASE_DIR / 'media'` assignment MAY
remain, but the `if not MEDIA_ROOT.exists(): MEDIA_ROOT.mkdir(...)` branch
MUST be removed.

#### Scenario: Settings import does not create media/

- GIVEN a clean checkout where `media/` does not yet exist
- WHEN `config.settings` is imported (e.g., via a management command or shell)
- THEN no `media/` directory SHALL be created on disk as a result of the import

#### Scenario: MEDIA_ROOT path is still declared

- GIVEN settings are loaded
- WHEN `settings.MEDIA_ROOT` is inspected
- THEN it SHALL equal `BASE_DIR / 'media'` (value unchanged; only the branch was removed)

### Requirement: REQ-2 — Media Directory Exists at Startup

After Django application startup, `MEDIA_ROOT` SHALL exist on disk, created
idempotently (no error on repeated boots).

#### Scenario: Directory created when missing

- GIVEN `MEDIA_ROOT` does not exist at app startup
- WHEN `CoreConfig.ready()` runs
- THEN `settings.MEDIA_ROOT` SHALL exist as a directory on disk

#### Scenario: Idempotent on repeated startup

- GIVEN `MEDIA_ROOT` already exists
- WHEN `CoreConfig.ready()` runs again (second boot)
- THEN no exception SHALL be raised and the directory SHALL still exist

### Requirement: REQ-3 — Tests Remain Unaffected

The project test runner (`config/test_runner.py`, `IsolatedMediaRunner`) SHALL
continue to redirect `MEDIA_ROOT` to a temporary directory for the whole suite
and clean it up, independent of where/when the real `media/` is created.

#### Scenario: Full suite passes

- GIVEN the change is applied
- WHEN `python manage.py test` runs
- THEN all tests SHALL pass and uploads during tests SHALL go to a temp MEDIA_ROOT

#### Scenario: Temp MEDIA_ROOT still isolated

- GIVEN `IsolatedMediaRunner.setup_test_environment` swaps `settings.MEDIA_ROOT`
- WHEN tests write uploaded files
- THEN those files SHALL be written under the temp directory, not the project `media/`
