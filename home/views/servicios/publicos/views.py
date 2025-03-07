from django.views.generic import ListView

from dashboard.models import Service

# Create your views here.

class PublicServicesListView(ListView):
    model = Service
    template_name = 'pages/home/servicios/publicos/servicios_publicos.html'
    context_object_name = 'pdf_list'
    paginate_by = 10

    def get_queryset(self):
        return Service.objects.filter(service_type=Service.PUBLIC).order_by('date')  # Ordenar por fecha

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Servicios Públicos'
        context['parent'] = 'servicios'
        context['segment'] = 'publicos'
        return context

