from django.utils import timezone
from django.views.generic import ListView

from apps.meteo.models import Warning as MeteoWarning


class EarlyWarningListView(ListView):
    model = MeteoWarning
    template_name = 'pages/home/warnings/early_warning.html'

    def get_queryset(self):
        return MeteoWarning.objects.filter(
            warning_type='early', valid_until__gte=timezone.now()
        ).select_related('user', 'user__profile')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Aviso de Alerta Temprana'
        context['parent'] = 'aviso'
        context['segment'] = 'warnings_early'
        context['objects'] = context['object_list']
        return context
