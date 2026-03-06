from django.utils import timezone
from dashboard.models import (
    EarlyWarning, StormWarning, TropicalCyclone,
    ServiceSubscription
)

def menu_notifications(request):
    context = {}
    now = timezone.now()

    # --- Avisos ---
    context['early_warning_count'] = EarlyWarning.objects.filter(valid_until__gte=now).count()
    context['tropical_cyclone_count'] = TropicalCyclone.objects.filter(valid_until__gte=now).count()
    context['storm_warning_count'] = StormWarning.objects.filter(valid_until__gte=now).count()

    # --- Suscripciones para staff (solo registros activos) ---
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        context['staff_requested_count'] = ServiceSubscription.objects.filter(
            payment_status='requested', record_active=True
        ).count()
        context['staff_pending_count'] = ServiceSubscription.objects.filter(
            payment_status='pending', record_active=True
        ).count()
        context['staff_expired_count'] = ServiceSubscription.objects.filter(
            payment_status='expired', record_active=True
        ).count()

    # --- Suscripciones para clientes (solo registros activos) ---
    if request.user.is_authenticated and hasattr(request.user, 'customer'):
        customer = request.user.customer
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
        context['client_pending_actions'] = context['client_requested_count'] + context['client_pending_count']
        context['client_total_notifications'] = context['client_pending_actions'] + context['client_expired_count']

    return context
