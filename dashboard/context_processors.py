from django.utils import timezone

from dashboard.models import (
    CustomerServiceSubscription,
    EarlyWarning,
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



def pending_subscriptions(request):
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        count = CustomerServiceSubscription.objects.filter(payment_status='pending').count()
        return {'pending_subscriptions_count': count}
    return {}
