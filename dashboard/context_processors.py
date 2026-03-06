from django.utils import timezone

from dashboard.models import (
    EarlyWarning,
    ServiceSubscription,
    StormWarning,
    TropicalCyclone,
)


def notification_counts(request):
    early_warning_count = EarlyWarning.objects.filter(valid_until__gte=timezone.now()).count()
    tropical_cyclone_count = TropicalCyclone.objects.filter(valid_until__gte=timezone.now()).count()
    storm_warning_count = StormWarning.objects.filter(valid_until__gte=timezone.now()).count()
    return {
        'early_warning_count': early_warning_count,
        'tropical_cyclone_count': tropical_cyclone_count,
        'storm_warning_count': storm_warning_count,
    }


def client_subscription_notifications(request):
    context = {}
    if request.user.is_authenticated and hasattr(request.user, 'customer'):
        customer = request.user.customer
        ahora = timezone.now()
        # Suscripciones activas (pagadas y no expiradas)
        context['client_active_count'] = ServiceSubscription.objects.filter(
            customer=customer,
            payment_status='paid',
            end_date__gt=ahora
        ).count()
        # Otros contadores
        context['client_requested_count'] = ServiceSubscription.objects.filter(
            customer=customer, payment_status='requested'
        ).count()
        context['client_pending_count'] = ServiceSubscription.objects.filter(
            customer=customer, payment_status='pending'
        ).count()
        context['client_expired_count'] = ServiceSubscription.objects.filter(
            customer=customer, payment_status='expired'
        ).count()
        context['client_pending_actions'] = context['client_requested_count'] + context['client_pending_count']
        context['client_total_notifications'] = context['client_pending_actions'] + context['client_expired_count']
    return context


def pending_subscriptions(request):
    context = {}
    
    # Para staff: conteos separados por estado (solicitudes, pendientes, expiradas)
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        context['staff_requested_count'] = ServiceSubscription.objects.filter(payment_status='requested').count()
        context['staff_pending_count'] = ServiceSubscription.objects.filter(payment_status='pending').count()
        context['staff_expired_count'] = ServiceSubscription.objects.filter(payment_status='expired').count()

    # Para clientes: suscripciones del cliente en estados solicitado, pendiente y expirado
    if request.user.is_authenticated and hasattr(request.user, 'customer'):
        customer = request.user.customer
        context['user_requested_count'] = ServiceSubscription.objects.filter(
            customer=customer,
            payment_status='requested'
        ).count()
        context['user_pending_count'] = ServiceSubscription.objects.filter(
            customer=customer,
            payment_status='pending'
        ).count()
        context['user_expired_count'] = ServiceSubscription.objects.filter(
            customer=customer,
            payment_status='expired'
        ).count()

    return context
