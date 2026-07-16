from django.core.management.base import BaseCommand
from django.utils import timezone

from dashboard.models import WeatherCommentary, WeatherNote, WeatherReport, WeatherToday, WeatherTomorrow


class Command(BaseCommand):
    help = "Migra datos de los modelos antiguos (WeatherToday, WeatherTomorrow, WeatherCommentary, WeatherNote) a WeatherReport."

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Solo mostrar cuántos registros se migrarían sin escribir en la DB.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        mappings = [
            (WeatherToday, 'today'),
            (WeatherTomorrow, 'tomorrow'),
            (WeatherCommentary, 'commentary'),
            (WeatherNote, 'note'),
        ]
        total_migrated = 0
        for old_model, report_type in mappings:
            qs = old_model.objects.all()
            count = qs.count()
            if count == 0:
                self.stdout.write(f"  {old_model.__name__}: 0 registros (sin datos)")
                continue
            if dry_run:
                self.stdout.write(f"  {old_model.__name__}: {count} registros listos para migrar")
                total_migrated += count
                continue
            migrated = 0
            for obj in qs:
                WeatherReport.objects.get_or_create(
                    uuid=obj.uuid,
                    defaults={
                        'user': obj.user,
                        'date': obj.date if hasattr(obj, 'date') and obj.date else timezone.now(),
                        'summary': obj.summary,
                        'file': obj.file,
                        'email_recipient_list': obj.email_recipient_list,
                        'type': report_type,
                    },
                )
                migrated += 1
            self.stdout.write(self.style.SUCCESS(f"  {old_model.__name__}: {migrated}/{count} registros migrados"))
            total_migrated += migrated

        if dry_run:
            self.stdout.write(self.style.WARNING(f"\nTotal: {total_migrated} registros listos para migrar."))
        else:
            self.stdout.write(self.style.SUCCESS(f"\nMigración completada: {total_migrated} registros migrados."))
