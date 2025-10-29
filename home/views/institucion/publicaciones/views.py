
from django.urls import reverse_lazy, reverse
from django.views.generic import *

from dashboard.models import StormWarning, ScientificPublication


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