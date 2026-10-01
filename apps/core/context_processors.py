import logging

from django.utils import timezone

from apps.core.models import SiteConfiguration
from apps.meteo.models import Warning

logger = logging.getLogger(__name__)


def site_branding(request):
    # Reuse the SiteConfiguration already fetched by MaintenanceModeMiddleware
    # when available; fall back to the singleton lookup otherwise.
    site_config = getattr(request, 'site_config', None)
    if site_config is None:
        site_config = SiteConfiguration.get_instance()
    return {'site_branding': site_config}


def menu_notifications(request):
    context = {}
    now = timezone.now()

    try:
        context['early_warning_count'] = Warning.objects.filter(
            warning_type='early', valid_until__gte=now
        ).count()
        context['tropical_cyclone_count'] = Warning.objects.filter(
            warning_type='tropical_cyclone', valid_until__gte=now
        ).count()
        context['storm_warning_count'] = Warning.objects.filter(
            warning_type='storm', valid_until__gte=now
        ).count()
    except Exception as e:
        logger.warning('Context processor query failed: %s', e)
        context['early_warning_count'] = 0
        context['tropical_cyclone_count'] = 0
        context['storm_warning_count'] = 0

    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        try:
            from django.db.models import Count, Q

            from apps.commercial.models import ServiceSubscription

            # Una sola consulta agregada en vez de un count por estado: los
            # badges salen en cada página del panel.
            counts = ServiceSubscription.objects.filter(record_active=True).aggregate(
                requested=Count('pk', filter=Q(payment_status='requested')),
                pending=Count('pk', filter=Q(payment_status='pending')),
            )
            context['staff_requested_count'] = counts['requested']
            context['staff_pending_count'] = counts['pending']
        except Exception as e:
            logger.warning('Staff counts query failed: %s', e)
            context['staff_requested_count'] = 0
            context['staff_pending_count'] = 0

    if request.user.is_authenticated and hasattr(request.user, 'commercial_customer'):
        try:
            from django.db.models import Count, Q

            from apps.commercial.models import ServiceSubscription

            customer = request.user.commercial_customer
            counts = ServiceSubscription.objects.filter(
                customer=customer, record_active=True
            ).aggregate(
                requested=Count('pk', filter=Q(payment_status='requested')),
                pending=Count('pk', filter=Q(payment_status='pending')),
                active=Count('pk', filter=Q(payment_status='paid', end_date__gt=now)),
                total=Count('pk'),
            )
            context['client_requested_count'] = counts['requested']
            context['client_pending_count'] = counts['pending']
            context['client_active_count'] = counts['active']
            # El total es lo que decide si "Mis Servicios" aparece: el cliente
            # lo necesita con cualquier suscripción, también pagada y vencida.
            context['client_subscriptions_count'] = counts['total']
            context['client_pending_actions'] = (
                context['client_requested_count'] + context['client_pending_count']
            )
        except Exception as e:
            logger.warning('Client counts query failed: %s', e)
            context['client_requested_count'] = 0
            context['client_pending_count'] = 0
            context['client_active_count'] = 0
            context['client_subscriptions_count'] = 0
            context['client_pending_actions'] = 0

    context.setdefault('early_warning_count', 0)
    context.setdefault('tropical_cyclone_count', 0)
    context.setdefault('storm_warning_count', 0)

    return context
