
from django.views.generic import ListView

from dashboard.models import ScientificPublication


class ScientificPublicationListView(ListView):
    template_name = 'pages/home/institucion/publicaciones/publicaciones.html'
    model = ScientificPublication

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Publicaciones Científicas'
        context['parent'] = 'institucion'
        context['segment'] = 'publicaciones_cientificas'
        context['objects'] = ScientificPublication.objects.all()
        return context