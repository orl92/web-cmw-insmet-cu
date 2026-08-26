from zoneinfo import ZoneInfo

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.meteo.models import Warning


class Command(BaseCommand):
    help = 'Normaliza Warning.valid_until: naive -> aware America/Havana. Idempotente.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply',
            action='store_true',
            help='Escribe los cambios. Por defecto es dry-run (no escribe).',
        )
        parser.add_argument(
            '--reverse',
            action='store_true',
            help='Quita la zona horaria (naive) para rollback de emergencia.',
        )

    def handle(self, *args, **options):
        apply = options['apply']
        reverse = options['reverse']
        if apply and reverse:
            self.stderr.write('No se puede usar --apply y --reverse a la vez.')
            return

        self.stdout.write(
            self.style.WARNING(
                'ADVERTENCIA: haz una copia de seguridad de la base de datos antes de usar --apply.'
            )
        )

        tz = ZoneInfo('America/Havana')
        changed = 0
        queryset = Warning.objects.filter(valid_until__isnull=False)

        for warning in queryset:
            value = warning.valid_until
            if reverse:
                if value.tzinfo is not None:
                    warning.valid_until = value.replace(tzinfo=None)
                    if apply:
                        warning.save(update_fields=['valid_until'])
                    changed += 1
            else:
                if value.tzinfo is None:
                    warning.valid_until = timezone.make_aware(value, tz)
                    if apply:
                        warning.save(update_fields=['valid_until'])
                    changed += 1

        mode = 'APPLY' if apply else 'DRY-RUN'
        self.stdout.write(self.style.SUCCESS(f'[{mode}] Filas afectadas: {changed}'))
