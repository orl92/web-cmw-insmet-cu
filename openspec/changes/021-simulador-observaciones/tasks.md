# Tasks: 021 — SYNOP Observation Simulator

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: pending
400-line budget risk: High

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~700 (range 640–760) |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 (generator) → PR 2 (CLI) → PR 3 (local mode + pipeline tests) |
| Delivery strategy | ask-on-risk |
| Chain strategy | pending |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: pending
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | `SynopSimulator` core + unit tests | PR 1 | `python manage.py test apps.api.tests.test_obs_simulator.SynopSimulatorUnitTests` | Python shell: build SM352.12 + SI352.03 bytes for 2026-09-14, assert header + session-2 layout | Delete `SynopSimulator.py` + `SynopSimulatorUnitTests` only |
| 2 | `generate_obs` CLI + package markers + command tests | PR 2 | `python manage.py test apps.api.tests.test_obs_simulator.GenerateObsCommandTests` | `python manage.py generate_obs --station 78352 --hour 12 --date 2026-09-14` → `media/obs/SM352.12`; `--station 99999` exits nonzero | Delete `apps/api/management/` + command tests; generator unaffected |
| 3 | `OBS_LOCAL_ONLY` local mode + realism + endpoint tests | PR 3 | `python manage.py test apps.api.tests.test_obs_simulator.SynopSimulatorRealismTests apps.api.tests.test_obs_simulator.ObsLocalModeEndpointTests` | `OBS_LOCAL_ONLY=1` runserver: GET `/api/station/observation/12/78352/` → 200 with no lftp; missing file → error naming path | Revert `config/settings.py` + `apps/api/data/FileObs.py`; delete realism + endpoint test classes |

## Phase 1: Setup

- [x] 1.1 `apps/api/management/__init__.py` — create empty package marker (directory does not exist)
- [x] 1.2 `apps/api/management/commands/__init__.py` — create empty package marker

## Phase 2: Generator (`apps/api/data/SynopSimulator.py`)

- [x] 2.1 Create `SynopSimulator.py` — class with `STATIONS = [78350..78355]`, `HOURS = ['00','03','06','09','12','15','18','21']`, `__init__(seed: int | None = None)`; deterministic int seed via `hashlib.md5(f"{station}:{date}:{hour}")` (D4)
- [x] 2.2 Header + session 1 — `AAXX YYGG1` (iW=1); fixed iR=1/iX=1 layout `IIiii iRixhVV Nddff 1SnTTT 2SnTdTdTd 3PPPP 4PPPP 5appp 6RRRtR 7wwW1W2 8NhCLCMCH 333 30///`; signed temps in tenths; pressure `int(round(p*10)) % 10000` (D1, D7)
- [x] 2.3 Diurnal T — `T(h) = 23.5 + 5.0·cos(2π(h−20)/24) + U(−1.2, 1.2)` clamped to [17.0, 30.5]; SM-only independent `Tx ∈ [29.5, 32.2]`, `Tn ∈ [15.5, 24.4]` (D2)
- [x] 2.4 Magnus Td — target RH ∈ [45, 92] → `Td = 243.5·ln(e/6.112)/(17.67−ln(e/6.112))`, `e = (RH/100)·e_s(T)`; guarantees `Td < T` and RH ∈ [38, 100] after 0.1 °C quantization (D3)
- [x] 2.5 Wind + clouds + pressure — `dd` from `Tablas.dd2` codes {03..09} (NE→E), `ff = randint(0, 7)`, `N = Nh` ∈ [0, 5]; station P ∈ [1011, 1015], sea P ∈ [1016, 1021] hPa (D5)
- [x] 2.6 Session 2 + close — SM: `10{0}{Tx:03d} 20{0}{Tn:03d} 30/// 56909 58012 81826=` + optional `7R24R24R24R24` (trace `9999`); SI: `56900 81825=`; close `NNNN`, no NULs (D7)
- [x] 2.7 Public API — `generate(station, hour, obs_date=None) -> str`, `generate_to_file(...) -> Path` (`SM{NN}.{HH}`/`SI{NN}.{HH}`), `generate_all(stations=None, hours=None, obs_date=None) -> list[Path]` (design interface)

## Phase 3: Local mode (settings flag + FileObs)

- [ ] 3.1 `config/settings.py` — add `OBS_LOCAL_ONLY = os.getenv('OBS_LOCAL_ONLY', '0') in ('1','true','True','yes')` after `FTP_OBS_PORT` (~line 405) with DEV-ONLY comment
- [ ] 3.2 `apps/api/data/FileObs.py` — in `descargar_archivos_por_hora`, after `makedirs` and before the lftp loop: `if settings.OBS_LOCAL_ONLY:` return existing `media/obs/{filename}`, else raise `FileNotFoundError` naming the path + `generate_obs` hint (D6; unset path byte-identical)

## Phase 4: CLI (`generate_obs`)

- [ ] 4.1 `apps/api/management/commands/generate_obs.py` — `BaseCommand`; options `--station`, `--hour` (repeatable), `--date` (default today UTC), `--output` (default `media/obs`); defaults all six stations / eight hours
- [ ] 4.2 Validation + run — `--station` outside `[78350..78355]` or invalid `--hour` → `CommandError` listing valid values (exit ≠ 0); create output dir; call `generate_all`

## Phase 5: Tests (`apps/api/tests/test_obs_simulator.py`)

- [x] 5.1 Create module — Django unittest (`SimpleTestCase` pure-unit, `APITestCase` HTTP), `SiteConfiguration` fixture like `test_api.py`, `_decode(text, station)` helper mirroring `OpenFileObs.station()`
- [x] 5.2 `SynopSimulatorUnitTests` — header `AAXX YYGG1`; SM s2 has `10`/`20` groups, SI s2 == `56900 81825=` without them; filename convention; same seed → identical bytes; validation errors; `Td < T` + RH ∈ [38, 100]
- [ ] 5.3 `GenerateObsCommandTests` — `call_command` writes `media/obs/SM352.12` for `--station 78352 --hour 12 --date 2026-09-14`; invalid station/hour raise `CommandError`
- [ ] 5.4 `SynopSimulatorRealismTests` — hours 03/09/12/18/21 same date via `Descodificador`: T ∈ [17, 30.5], T(18)/T(21) ≥ T(09)/T(12), RH ∈ [38, 100], sky ∈ {Despejado, Poco nublado, Parcialmente nublado}, Nh ≤ 5, station/sea-P ranges, SM Tx/Tn ranges, dd azimuth NE→E
- [ ] 5.5 `ObsLocalModeEndpointTests` — `setUp` writes today-dated `media/obs/SM352.12` + `addCleanup`; `override_settings(OBS_LOCAL_ONLY=True)` + `mock.patch('subprocess.run', side_effect=AssertionError)` → GET observation (12, 78352) = 200 and run never called; missing file → `FileNotFoundError` naming `media/obs`; flag unset → lftp path reached (`time.sleep` patched)

## Phase 6: Verification

- [ ] 6.1 `python manage.py check` — no errors
- [ ] 6.2 `python manage.py test apps.api` — full api suite passes (incl. `test_obs_simulator`)
- [ ] 6.3 `ruff check apps/api config/settings.py` + `pre-commit run --all-files` — clean (no templates touched, djlint N/A)