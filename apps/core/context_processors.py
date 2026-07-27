import logging

from django.utils import timezone

from apps.meteo.models import Warning

logger = logging.getLogger(__name__)


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
        logger.warning("Context processor query failed: %s", e)
        context['early_warning_count'] = 0
        context['tropical_cyclone_count'] = 0
        context['storm_warning_count'] = 0

    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        try:
            from apps.commercial.models import ServiceSubscription
            context['staff_requested_count'] = ServiceSubscription.objects.filter(
                payment_status='requested', record_active=True
            ).count()
            context['staff_pending_count'] = ServiceSubscription.objects.filter(
                payment_status='pending', record_active=True
            ).count()
            context['staff_expired_count'] = ServiceSubscription.objects.filter(
                payment_status='expired', record_active=True
            ).count()
        except Exception as e:
            logger.warning("Staff counts query failed: %s", e)
            context['staff_requested_count'] = 0
            context['staff_pending_count'] = 0
            context['staff_expired_count'] = 0

    if request.user.is_authenticated and hasattr(request.user, 'commercial_customer'):
        try:
            from apps.commercial.models import ServiceSubscription
            customer = request.user.commercial_customer
            context['client_requested_count'] = ServiceSubscription.objects.filter(
                customer=customer, payment_status='requested', record_active=True
            ).count()
            context['client_pending_count'] = ServiceSubscription.objects.filter(
                customer=customer, payment_status='pending', record_active=True
            ).count()
            context['client_expired_count'] = ServiceSubscription.objects.filter(
                customer=customer, payment_status='expired', record_active=True
            ).count()
            context['client_active_count'] = ServiceSubscription.objects.filter(
                customer=customer, payment_status='paid', end_date__gt=now, record_active=True
            ).count()
        except Exception as e:
            logger.warning("Client counts query failed: %s", e)
            context['client_requested_count'] = 0
            context['client_pending_count'] = 0
            context['client_expired_count'] = 0
            context['client_active_count'] = 0
            context['client_pending_actions'] = 0
            context['client_total_notifications'] = 0

    context.setdefault('early_warning_count', 0)
    context.setdefault('tropical_cyclone_count', 0)
    context.setdefault('storm_warning_count', 0)

    return context
