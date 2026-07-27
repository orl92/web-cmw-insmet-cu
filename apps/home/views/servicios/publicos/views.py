from django.views.generic import ListView

from apps.commercial.models import Service

# Create your views here.

class PublicServicesListView(ListView):
    model = Service
    template_name = 'pages/home/services/public.html'
    context_object_name = 'pdf_list'
    paginate_by = 10

    def get_queryset(self):
        return Service.objects.filter(service_type=Service.PUBLIC).order_by('date').select_related('user')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Servicios Públicos'
        context['parent'] = 'servicios'
        context['segment'] = 'publicos'
        return context
