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

        # Obtener objetos y agregar URLs absolutas
        objects = self.get_queryset()
        for obj in objects:
            if obj.file:
                # Agregar URL absoluta al objeto
                obj.absolute_file_url = self.request.build_absolute_uri(obj.file.url)

        context['objects'] = objects
        return context
