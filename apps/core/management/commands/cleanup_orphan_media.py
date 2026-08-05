import os

from django.apps import apps
from django.core.management.base import BaseCommand
from django.db.models import FileField, ImageField


class Command(BaseCommand):
    help = 'Elimina archivos huérfanos de MEDIA_ROOT (pdf/ e img/) no referenciados en la BD'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Lista los archivos huérfanos sin borrarlos',
        )

    def handle(self, *args, **options):
        from django.conf import settings

        dry_run = options['dry_run']
        media_root = settings.MEDIA_ROOT

        referenced = self._collect_referenced()

        orphans = []
        for subdir in ('pdf', 'img'):
            base = media_root / subdir
            if not base.exists():
                continue
            for root, _dirs, files in os.walk(base):
                for fname in files:
                    rel = os.path.join(root, fname)
                    rel_name = os.path.relpath(rel, media_root)
                    if rel_name not in referenced:
                        orphans.append(rel)

        if not orphans:
            self.stdout.write(self.style.SUCCESS('No hay archivos huérfanos.'))
            return

        for path in orphans:
            rel = os.path.relpath(path, media_root)
            if dry_run:
                self.stdout.write(self.style.WARNING(f'[dry-run] {rel}'))
            else:
                os.remove(path)
                self.stdout.write(f'Eliminado: {rel}')

        self.stdout.write(self.style.SUCCESS(
            f"{'Se eliminarían' if dry_run else 'Eliminados'} {len(orphans)} archivo(s) huérfano(s)."
        ))

    def _collect_referenced(self):
        referenced = set()
        for model in apps.get_models():
            for field in model._meta.fields:
                if isinstance(field, (FileField, ImageField)):
                    qs = model.objects.exclude(**{field.name: ''})
                    for value in qs.values_list(field.name, flat=True):
                        if value:
                            referenced.add(value)
        return referenced
