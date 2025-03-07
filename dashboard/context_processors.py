from django.utils import timezone

from dashboard.models import (EarlyWarning, RadarWarning, SpecialNotice,
                              TropicalCyclone)


def notification_counts(request):
    early_warning_count = EarlyWarning.objects.filter(valid_until__gte=timezone.now()).count()
    tropical_cyclone_count = TropicalCyclone.objects.filter(valid_until__gte=timezone.now()).count()
    special_notice_count = SpecialNotice.objects.filter(valid_until__gte=timezone.now()).count()
    radar_warning_count = RadarWarning.objects.filter(valid_until__gte=timezone.now()).count()
    return {
        'early_warning_count': early_warning_count,
        'tropical_cyclone_count': tropical_cyclone_count,
        'special_notice_count': special_notice_count,
        'radar_warning_count': radar_warning_count,
    }
