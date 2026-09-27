"""Management command to simulate SYNOP observations offline.

DEV tooling: writes fake ``SM{NN}.{HH}`` / ``SI{NN}.{HH}`` observation files
for the six Camagüey stations (78350-78355) so the pipeline
``FileObs -> OpenFileObs -> Descodificador -> GetData`` can be exercised
without the INSMET FTPS server — fully offline, no network, no lftp.

The files feed the same ``media/obs`` directory the production downloader
uses; named per the existing convention (``NN = str(station)[2:]``).
"""

from datetime import UTC, date, datetime
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.api.data.SynopSimulator import SynopSimulator


class Command(BaseCommand):
    help = (
        'Generate simulated SYNOP observation files (SM{NN}.{HH}/SI{NN}.{HH}) for the '
        'six Camagüey stations (78350-78355). DEV tooling: the fake observations let the '
        'FileObs -> OpenFileObs -> Descodificador pipeline run without the INSMET FTP '
        'server (offline, no lftp).'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--station',
            type=int,
            default=None,
            help='Station number to generate (default: all six stations 78350-78355).',
        )
        parser.add_argument(
            '--hour',
            action='append',
            default=None,
            help=('Observation hour, repeatable (default: all of 00/03/06/09/12/15/18/21).'),
        )
        parser.add_argument(
            '--date',
            default=None,
            help='Observation date as YYYY-MM-DD (default: today UTC).',
        )
        parser.add_argument(
            '--output',
            default='media/obs',
            help='Output directory for the generated files (default: media/obs).',
        )

    def handle(self, *args, **options):
        station = options['station']
        hours = options['hour']
        obs_date = self._parse_date(options['date'])
        output_dir = Path(options['output'])

        if station is not None and station not in SynopSimulator.STATIONS:
            raise CommandError(
                f'Invalid station {station}. Valid stations: {SynopSimulator.STATIONS}'
            )

        if hours is None:
            hours = SynopSimulator.HOURS
        elif isinstance(hours, str):
            hours = [hours]
        invalid_hours = [hour for hour in hours if hour not in SynopSimulator.HOURS]
        if invalid_hours:
            raise CommandError(
                f'Invalid hour(s) {invalid_hours}. Valid hours: {SynopSimulator.HOURS}'
            )

        stations = [station] if station is not None else None
        output_dir.mkdir(parents=True, exist_ok=True)
        paths = SynopSimulator().generate_all(output_dir, stations, hours, obs_date)
        self.stdout.write(
            self.style.SUCCESS(f'Generated {len(paths)} SYNOP file(s) in {output_dir}')
        )

    @staticmethod
    def _parse_date(value):
        """Return the observation date, defaulting to today UTC.

        Accepts a ``date``/``datetime`` (``call_command`` passes objects
        straight through) or a ``YYYY-MM-DD`` string (the CLI form); anything
        else raises :class:`CommandError` listing the expected format.
        """
        if value is None:
            return datetime.now(UTC).date()
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        try:
            return date.fromisoformat(value)
        except TypeError, ValueError:
            raise CommandError(
                f'Invalid date {value!r}. Use YYYY-MM-DD (e.g. 2026-09-14).'
            ) from None
