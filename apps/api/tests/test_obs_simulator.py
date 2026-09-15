"""Unit tests for the offline SYNOP observation simulator.

Covers the generator contract from change 021 (OBS-SIM-GENERATOR): header
encoding, session-1 layout (design D1), SM/SI session-2 differences, filename
convention, deterministic seeds and validation errors; plus the realism bounds
(OBS-SIM-REALISM) that hold at construction time: ``Td < T`` and
``38 <= RH <= 100``.

Work unit 1 scope: only :class:`SynopSimulatorUnitTests` and the ``_decode``
helper. The decode-through-``Descodificador`` realism and the local-endpoint
test classes land with work units 2/3.
"""

import math
import tempfile
from datetime import date

from django.test import SimpleTestCase

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
