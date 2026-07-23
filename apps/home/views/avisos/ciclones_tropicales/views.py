from django.utils import timezone
from django.views.generic import ListView

from apps.dashboard.models import TropicalCyclone


class TropicalCycloneListView(ListView):
    model = TropicalCyclone
    template_name = 'pages/home/avisos/ciclon_tropical.html'

    def get_queryset(self):
        return TropicalCyclone.objects.filter(valid_until__gte=timezone.now()).select_related('user')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Aviso de Ciclón Tropical'
        context['parent'] = 'aviso'
        context['segment'] = 'warnings_tropical'
        
        # Obtener objetos y agregar URLs absolutas
        objects = self.get_queryset()
        for obj in objects:
            if obj.file:
                # Agregar URL absoluta al objeto
                obj.absolute_file_url = self.request.build_absolute_uri(obj.file.url)
        
        context['objects'] = objects
        return context
