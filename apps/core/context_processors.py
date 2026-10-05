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

    # `request.user` no siempre existe: lo pone AuthenticationMiddleware, que va
    # DESPUES de SecurityMiddleware y CommonMiddleware. Si cualquiera de esos dos
    # levanta una excepcion (un Host no permitido, por ejemplo), Django entra al
    # handler de error con una request que todavia no tiene `.user`, y aca el
    # AttributeError tapa el error real con un 500: el cliente ve "error interno"
    # en lugar del 400 que corresponde, y el log muestra el context processor en
    # vez de la causa.
    #
    # O sea: los handlers de error de este proyecto (apps/core/utils.py) renderizan
    # plantillas, y toda plantilla pasa por este context processor. Sin el getattr,
    # la pagina de error se cae sola, que es el peor momento para que se caiga.
    user = getattr(request, 'user', None)

    if user is not None and user.is_authenticated and (user.is_staff or user.is_superuser):
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

    if user is not None and user.is_authenticated and hasattr(user, 'commercial_customer'):
        try:
            from django.db.models import Count, Q

            from apps.commercial.models import ServiceSubscription

            customer = user.commercial_customer
            counts = ServiceSubscription.objects.filter(
                customer=customer, record_active=True
            ).aggregate(
                requested=Count('pk', filter=Q(payment_status='requested')),
                pending=Count('pk', filter=Q(payment_status='pending')),
                active=Count('pk', filter=Q(payment_status='paid')),
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
