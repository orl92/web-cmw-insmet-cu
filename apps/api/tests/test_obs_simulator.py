"""Unit tests for the offline SYNOP observation simulator.

Covers the generator contract from change 021 (OBS-SIM-GENERATOR): header
encoding, session-1 layout (design D1), SM/SI session-2 differences, filename
convention, deterministic seeds and validation errors; plus the realism bounds
(OBS-SIM-REALISM) that hold at construction time: ``Td < T`` and
``38 <= RH <= 100``.

Work unit 1 scope: only :class:`SynopSimulatorUnitTests` and the ``_decode``
helper. Work unit 2 adds :class:`GenerateObsCommandTests` for the
``generate_obs`` management command.  Work unit 3 adds
:class:`SynopSimulatorRealismTests` (decode-through-``Descodificador`` realism)
and :class:`ObsLocalModeEndpointTests` (OBS_LOCAL_ONLY endpoint path).
"""

import math
import os
import tempfile
from datetime import UTC, date, datetime
from pathlib import Path
from unittest import mock

from django.core.cache import cache
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from apps.api.data.SynopSimulator import SynopSimulator


def _magnus_es(t):
    """Saturation vapour pressure in hPa via the Magnus formula (same as Descodificador)."""
    return 6.112 * math.exp((17.67 * t) / (t + 243.5))


def _decode(text, station):
    """Mirror ``OpenFileObs.station()`` over in-memory text (no filesystem).

    The real parser reads raw file lines, finds the line containing the station
    number and takes the next line as session 2; the header's last token
    carries ``YYGGi``. This helper replicates that exact behaviour so unit
    tests never touch ``media/``.
    """
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    header = lines[0].split()[-1]
    decoded = {
        'day': header[:2],
        'hour': header[2:4],
        'number': station,
        'sesion1': None,
        'sesion2': None,
    }
    for i, line in enumerate(lines):
        if str(station) in line:
            decoded['sesion1'] = line
            if i + 1 < len(lines):
                decoded['sesion2'] = lines[i + 1]
    return decoded


def _nin_tenths(token):
    """Decode the signed temperature value inside a ``1SnTTT``/``2SnTdTdTd`` token."""
    sign = -1 if token[1] == '1' else 1
    return sign * int(token[2:])


class SynopSimulatorUnitTests(SimpleTestCase):
    """Pure unit tests for the simulator (tasks 2.1-2.7 and 5.1-5.2)."""

    def test_header_encodes_day_hour_and_iw1(self):
        text = SynopSimulator().generate(78352, '12', date(2026, 9, 14))
        self.assertEqual(text.splitlines()[0], 'AAXX 14121')

    def test_header_other_day_and_hour(self):
        text = SynopSimulator().generate(78352, '03', date(2026, 9, 3))
        self.assertEqual(text.splitlines()[0], 'AAXX 03031')

    def test_file_closes_with_nnnn_and_has_no_nuls(self):
        text = SynopSimulator().generate(78350, '00', date(2026, 9, 14))
        self.assertTrue(text.rstrip('\n').endswith('\nNNNN'))
        self.assertNotIn('\x00', text)

    def test_session1_layout_indexes_for_decoder(self):
        """D1: with iR=1, iX=1 the ``8NhCLCMCH`` group must sit at token index 10."""
        text = SynopSimulator().generate(78352, '12', date(2026, 9, 14))
        tokens = _decode(text, 78352)['sesion1'].split()
        self.assertEqual(len(tokens), 13)
        self.assertTrue(tokens[8].startswith('6'), tokens)  # 6RRRtR
        self.assertTrue(tokens[9].startswith('7'), tokens)  # 7wwW1W2
        self.assertTrue(tokens[10].startswith('8'), tokens)  # 8NhCLCMCH
        self.assertEqual(tokens[11], '333')
        self.assertEqual(tokens[12], '30///')

    def test_sm_session2_has_tx_and_tn_groups(self):
        text = SynopSimulator().generate(78352, '12', date(2026, 9, 14))
        groups = _decode(text, 78352)['sesion2'].split()
        self.assertTrue(any(group.startswith('10') for group in groups), groups)
        self.assertTrue(any(group.startswith('20') for group in groups), groups)
        self.assertTrue(any(group.endswith('=') for group in groups), groups)

    def test_si_session2_is_exact_without_tx_tn(self):
        text = SynopSimulator().generate(78352, '03', date(2026, 9, 14))
        decoded = _decode(text, 78352)
        self.assertEqual(decoded['sesion2'], '56900 81825=')
        self.assertFalse(
            any(group.startswith(('10', '20')) for group in decoded['sesion2'].split())
        )

    def test_station_number_opens_session1(self):
        text = SynopSimulator().generate(78355, '06', date(2026, 9, 14))
        decoded = _decode(text, 78355)
        self.assertEqual(decoded['number'], 78355)
        self.assertTrue(decoded['sesion1'].startswith('78355'))

    def test_filename_convention(self):
        sim = SynopSimulator()
        with tempfile.TemporaryDirectory() as tmp:
            for station, hour, expected in [
                (78352, '12', 'SM352.12'),
                (78352, '03', 'SI352.03'),
                (78350, '00', 'SM350.00'),
                (78355, '21', 'SI355.21'),
            ]:
                with self.subTest(filename=expected):
                    path = sim.generate_to_file(station, hour, date(2026, 9, 14), tmp)
                    self.assertEqual(path.name, expected)
                    self.assertTrue(path.exists())
                    self.assertEqual(
                        path.read_text(), sim.generate(station, hour, date(2026, 9, 14))
                    )

    def test_generate_all_writes_complete_grid(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = SynopSimulator().generate_all(
                tmp, stations=[78350, 78351], hours=['00', '03'], obs_date=date(2026, 9, 14)
            )
            self.assertEqual(len(paths), 4)
            self.assertEqual(
                sorted(path.name for path in paths),
                ['SI350.03', 'SI351.03', 'SM350.00', 'SM351.00'],
            )

    def test_same_seed_produces_identical_bytes(self):
        obs_date = date(2026, 9, 14)
        self.assertEqual(
            SynopSimulator(seed=42).generate(78352, '12', obs_date),
            SynopSimulator(seed=42).generate(78352, '12', obs_date),
        )
        # Default instances must be deterministic too (MD5-derived seed, D4).
        self.assertEqual(
            SynopSimulator().generate(78352, '12', obs_date),
            SynopSimulator().generate(78352, '12', obs_date),
        )

    def test_same_seed_still_varies_per_observation(self):
        obs_date = date(2026, 9, 14)
        self.assertNotEqual(
            SynopSimulator(seed=1).generate(78350, '12', obs_date),
            SynopSimulator(seed=1).generate(78351, '12', obs_date),
        )

    def test_invalid_station_raises_value_error(self):
        sim = SynopSimulator()
        for station in (99999, 78349, 78356):
            with self.subTest(station=station), self.assertRaises(ValueError):
                sim.generate(station, '12', date(2026, 9, 14))

    def test_invalid_hour_raises_value_error(self):
        sim = SynopSimulator()
        for hour in ('25', '99', '30'):
            with self.subTest(hour=hour), self.assertRaises(ValueError):
                sim.generate(78352, hour, date(2026, 9, 14))

    def test_td_lt_t_and_rh_in_range_for_all_hours(self):
        sim = SynopSimulator()
        obs_date = date(2026, 9, 14)
        for hour in SynopSimulator.HOURS:
            with self.subTest(hour=hour):
                tokens = _decode(sim.generate(78352, hour, obs_date), 78352)['sesion1'].split()
                t = _nin_tenths(tokens[3]) / 10
                td = _nin_tenths(tokens[4]) / 10
                self.assertLess(td, t)
                rh = 100 * _magnus_es(td) / _magnus_es(t)
                self.assertGreaterEqual(rh, 38)
                self.assertLessEqual(rh, 100)


class GenerateObsCommandTests(SimpleTestCase):
    """Management command ``generate_obs`` (tasks 4.1, 4.2, 5.3).

    Exercises the CLI contract from OBS-SIM-GENERATOR through
    ``call_command``: option defaults, SM/SI file writing, output-dir
    creation, the today-UTC default date, and the ``CommandError`` paths for
    invalid station, hour and date. Every run uses a temporary output
    directory so ``media/obs`` (real downloads) is never touched.
    """

    def test_generates_sm_file_at_explicit_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            call_command(
                'generate_obs',
                station=78352,
                hour='12',
                date=date(2026, 9, 14),
                output=tmp,
            )
            path = Path(tmp) / 'SM352.12'
            self.assertTrue(path.exists(), 'SM352.12 was not written')
            text = path.read_text()
            self.assertEqual(text.splitlines()[0], 'AAXX 14121')
            session2 = _decode(text, 78352)['sesion2'].split()
            self.assertTrue(any(g.startswith('10') for g in session2), session2)
            self.assertTrue(any(g.startswith('20') for g in session2), session2)

    def test_generates_si_file_without_tx_tn(self):
        with tempfile.TemporaryDirectory() as tmp:
            call_command(
                'generate_obs',
                station=78352,
                hour='03',
                date=date(2026, 9, 14),
                output=tmp,
            )
            path = Path(tmp) / 'SI352.03'
            self.assertTrue(path.exists(), 'SI352.03 was not written')
            text = path.read_text()
            self.assertEqual(text.splitlines()[0], 'AAXX 14031')
            self.assertEqual(_decode(text, 78352)['sesion2'], '56900 81825=')

    def test_output_directory_is_created_when_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'nested' / 'obs'
            call_command(
                'generate_obs',
                station=78350,
                hour='00',
                date=date(2026, 9, 14),
                output=str(output),
            )
            self.assertTrue((output / 'SM350.00').exists())

    def test_defaults_generate_all_stations_and_hours(self):
        with tempfile.TemporaryDirectory() as tmp:
            call_command('generate_obs', output=tmp)
            names = {path.name for path in Path(tmp).iterdir()}
            expected = {
                SynopSimulator.filename_for(station, hour)
                for station in SynopSimulator.STATIONS
                for hour in SynopSimulator.HOURS
            }
            self.assertEqual(len(names), len(SynopSimulator.STATIONS) * len(SynopSimulator.HOURS))
            self.assertEqual(names, expected)

    def test_default_date_is_today_utc(self):
        with tempfile.TemporaryDirectory() as tmp:
            before = datetime.now(UTC).date()
            call_command('generate_obs', station=78352, hour='12', output=tmp)
            after = datetime.now(UTC).date()
            header = (Path(tmp) / 'SM352.12').read_text().splitlines()[0]
            self.assertIn(header, {f'AAXX {day.day:02d}121' for day in (before, after)})

    def test_invalid_station_list_valid_stations(self):
        for station in (99999, 78349):
            with self.subTest(station=station):
                with tempfile.TemporaryDirectory() as tmp, self.assertRaises(CommandError) as ctx:
                    call_command(
                        'generate_obs',
                        station=station,
                        hour='12',
                        date=date(2026, 9, 14),
                        output=tmp,
                    )
                self.assertIn('78350', str(ctx.exception))
                self.assertIn('78355', str(ctx.exception))

    def test_invalid_hour_list_valid_hours(self):
        with tempfile.TemporaryDirectory() as tmp, self.assertRaises(CommandError) as ctx:
            call_command(
                'generate_obs',
                station=78352,
                hour='25',
                date=date(2026, 9, 14),
                output=tmp,
            )
        self.assertIn("'00'", str(ctx.exception))
        self.assertIn("'21'", str(ctx.exception))

    def test_invalid_date_raises_command_error(self):
        for bad in ('2026-02-30', 'not-a-date', '14/09/2026'):
            with (
                self.subTest(bad=bad),
                tempfile.TemporaryDirectory() as tmp,
                self.assertRaises(CommandError),
            ):
                call_command(
                    'generate_obs',
                    station=78352,
                    hour='12',
                    date=bad,
                    output=tmp,
                )


class SynopSimulatorRealismTests(SimpleTestCase):
    """Decode-through-``Descodificador`` realism tests (task 5.4, OBS-SIM-REALISM).

    Generates observations at hours 03/09/12/18/21 for the same date, then
    decodes them through the full ``Descodificador`` pipeline (mirroring the
    real data path) and asserts that every decoded value falls inside the
    plausible Camagüey September climate window.
    """

    def setUp(self):
        super().setUp()
        self.obs_date = date.today()
        self.sim = SynopSimulator()
        self.station = 78352
        self._test_hours = ['03', '09', '12', '18', '21']

    def _decoded(self, hour):
        """Generate and decode one observation through ``Descodificador``."""
        from apps.api.data.Descodificador import Descodificador

        text = self.sim.generate(self.station, hour, self.obs_date)
        obs = _decode(text, self.station)
        return Descodificador(obs)

    def _decode_pressure(self, pppp_str):
        """Decode a 4-digit PPPP group (thousands digit omitted) to hPa."""
        p = int(pppp_str)
        if p < 1000:
            p += 10000
        return p / 10.0

    def test_temperature_in_range(self):
        """T in [17.0, 30.5] degC for every test hour."""
        for h in self._test_hours:
            with self.subTest(hour=h):
                d = self._decoded(h)
                t = d.get_temp()
                self.assertIsNotNone(t, f'get_temp() returned None for hour {h}')
                self.assertGreaterEqual(t, 17.0)
                self.assertLessEqual(t, 30.5)

    def test_diurnal_cycle(self):
        """T(18)/T(21) >= T(09)/T(12) — afternoon/night warmer than morning."""
        temps = {h: self._decoded(h).get_temp() for h in self._test_hours}
        for warm in ('18', '21'):
            for cold in ('09', '12'):
                self.assertGreaterEqual(
                    temps[warm],
                    temps[cold],
                    f'T({warm})={temps[warm]} should be >= T({cold})={temps[cold]}',
                )

    def test_relative_humidity_in_range(self):
        """RH in [38, 100] % for every test hour."""
        for h in self._test_hours:
            with self.subTest(hour=h):
                d = self._decoded(h)
                rh = d.get_rh()
                self.assertIsNotNone(rh, f'get_rh() returned None for hour {h}')
                self.assertGreaterEqual(rh, 38)
                self.assertLessEqual(rh, 100)

    def test_sky_state_plausible(self):
        """get_estado_cielo() is one of the three allowed sky texts."""
        allowed = {'Despejado', 'Poco nublado', 'Parcialmente nublado'}
        for h in self._test_hours:
            with self.subTest(hour=h):
                sky = self._decoded(h).get_estado_cielo()
                self.assertIn(sky, allowed, f'Unexpected sky text for hour {h}')

    def test_cielo_cubierto_max_5(self):
        """Nh (get_cielo_cubierto()) <= 5 octas for every test hour."""
        for h in self._test_hours:
            with self.subTest(hour=h):
                nh = self._decoded(h).get_cielo_cubierto()
                self.assertIsNotNone(nh)
                self.assertLessEqual(nh, 5)

    def test_pressure_station_range(self):
        """Station pressure (3PPPP) in [1011, 1015] hPa."""
        for h in self._test_hours:
            with self.subTest(hour=h):
                d = self._decoded(h)
                p = self._decode_pressure(d.fm12._3PPPP)
                self.assertGreaterEqual(p, 1011.0)
                self.assertLessEqual(p, 1015.0)

    def test_pressure_sea_range(self):
        """Sea-level pressure (4PPPP) in [1016, 1021] hPa."""
        for h in self._test_hours:
            with self.subTest(hour=h):
                d = self._decoded(h)
                p = self._decode_pressure(d.fm12._4PPPP)
                self.assertGreaterEqual(p, 1016.0)
                self.assertLessEqual(p, 1021.0)

    def test_sm_tx_range(self):
        """Tx (max temperature) in [29.5, 32.2] degC for SM hours."""
        for h in SynopSimulator.SM_HOURS:
            with self.subTest(hour=h):
                d = self._decoded(h)
                tx = d.get_tempTx()
                self.assertIsNotNone(tx, f'get_tempTx() returned None for SM hour {h}')
                self.assertGreaterEqual(tx, 29.5)
                self.assertLessEqual(tx, 32.2)

    def test_sm_tn_range(self):
        """Tn (min temperature) in [15.5, 24.4] degC for SM hours."""
        for h in SynopSimulator.SM_HOURS:
            with self.subTest(hour=h):
                d = self._decoded(h)
                tn = d.get_tempTn()
                self.assertIsNotNone(tn, f'get_tempTn() returned None for SM hour {h}')
                self.assertGreaterEqual(tn, 15.5)
                self.assertLessEqual(tn, 24.4)

    def test_wind_direction_ne_to_e(self):
        """dd2 (get_ddViento2()) in [45, 90] — trade-wind azimuth NE to E."""
        for h in self._test_hours:
            with self.subTest(hour=h):
                dd = self._decoded(h).get_ddViento2()
                self.assertIsNotNone(dd)
                self.assertGreaterEqual(dd, 45)
                self.assertLessEqual(dd, 90)


class ObsLocalModeEndpointTests(APITestCase):
    """OBS_LOCAL_ONLY endpoint tests (task 5.5, OBS-LOCAL-ONLY-MODE).

    Exercises the three spec scenarios: local file served without FTP,
    missing local file fails clearly, and the default path keeps lftp.
    """

    def setUp(self):
        super().setUp()
        cache.clear()
        from apps.core.models import SiteConfiguration

        SiteConfiguration.objects.get_or_create(defaults={'maintenance_mode': False})

        # Generate a fresh today-dated SM352.12 for the endpoint.
        obs_date = date.today()
        self.sim = SynopSimulator()
        text = self.sim.generate(78352, '12', obs_date)
        self.filepath = os.path.normpath(os.path.join('media', 'obs', 'SM352.12'))
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        with open(self.filepath, 'w', encoding='utf-8') as f:
            f.write(text)
        self.addCleanup(self._cleanup_file)

    def _cleanup_file(self):
        cache.clear()
        if os.path.exists(self.filepath):
            os.remove(self.filepath)

    @override_settings(OBS_LOCAL_ONLY=True)
    @mock.patch(
        'apps.api.data.FileObs.subprocess.run',
        side_effect=AssertionError('subprocess.run must NOT be called in local mode'),
    )
    def test_local_file_served_without_ftp(self, mock_run):
        """Scenario: local file served without FTP — 200 + no subprocess.run."""
        url = '/api/station/observation/12/78352/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data['data']['temperatura'], (int, float))
        mock_run.assert_not_called()

    @override_settings(OBS_LOCAL_ONLY=True)
    def test_missing_local_file_raises_error(self):
        """Scenario: missing local file fails clearly — FileNotFoundError."""
        from apps.api.data.FileObs import FileObs

        fileobs = FileObs()
        with self.assertRaises(FileNotFoundError) as ctx:
            # SI351.03 does not exist locally (nor in real media/obs).
            fileobs.descargar_archivos_por_hora('03', 78351)
        self.assertIn('media/obs', str(ctx.exception))

    @mock.patch('apps.api.data.FileObs.time.sleep')
    @mock.patch(
        'apps.api.data.FileObs.subprocess.run',
        side_effect=FileNotFoundError('lftp: not found'),
    )
    def test_default_path_reaches_lftp_loop(self, mock_run, mock_sleep):
        """Scenario: default path keeps lftp — subprocess.run IS called."""
        from apps.api.data.FileObs import FileObs

        fileobs = FileObs()
        with self.assertRaises(FileNotFoundError):
            fileobs.descargar_archivos_por_hora('12', 78351)
        # The retry loop calls subprocess.run max_retries (3) times.
        self.assertEqual(mock_run.call_count, 3)
