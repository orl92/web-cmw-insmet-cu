from django.views.generic import ListView

from apps.publications.models import ScientificPublication


class ScientificPublicationListView(ListView):
    template_name = 'pages/home/institution/publications.html'
    model = ScientificPublication

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Publicaciones Científicas'
        context['parent'] = 'institucion'
        context['segment'] = 'publicaciones_cientificas'
        context['objects'] = (
            ScientificPublication.objects.all()
            .select_related('author')
            .prefetch_related('coauthors')
        )
        return context
