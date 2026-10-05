"""Rellena `Invoice.subscription` en las facturas que quedaron sin ancla.

La facturación por lote agrupa varias suscripciones y deja el campo en NULL a
propósito (no hay una respuesta única); el vínculo real vive en cada línea. Ese
campo se completa cuando la factura cubre una sola suscripción, para que
`subscription.invoices` —la relación que consulta el código y los templates—
deje de devolver vacío.

Es idempotente: sólo actúa sobre facturas huérfanas de una sola suscripción.
"""

from django.core.management.base import BaseCommand
from django.db.models import Count

from apps.commercial.models import Invoice, ServiceSubscription


class Command(BaseCommand):
    help = 'Enlaza a su suscripción las facturas huérfanas que cubren una sola suscripción.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra qué facturas se modificarían sin escribir nada.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        candidates = (
            Invoice.objects.filter(subscription__isnull=True)
            .annotate(subs=Count('items__subscription', distinct=True))
            .filter(subs=1)
        )

        total = candidates.count()
        if not total:
            self.stdout.write(self.style.SUCCESS('No hay facturas huérfanas que reparar.'))
            return

        for invoice in candidates.select_related('customer'):
            sub_id = (
                invoice.items.exclude(subscription__isnull=True)
                .values_list('subscription_id', flat=True)
                .first()
            )
            invoice.subscription = ServiceSubscription.objects.get(pk=sub_id)
            self.stdout.write(
                f'  {invoice.number} -> suscripción {invoice.subscription_id} ({invoice.customer})'
            )
            if not dry_run:
                invoice.save(update_fields=['subscription'])

        prefix = 'Se repararían' if dry_run else 'Se repararon'
        verb = self.style.SUCCESS if not dry_run else self.style.WARNING
        self.stdout.write(verb(f'{prefix} {total} factura(s).'))
        if dry_run:
            self.stdout.write('Sin cambios: usar sin --dry-run para aplicarlo.')
