from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

from dashboard.models import Service

# Create your views here.


class CommercialServicesListView(LoginRequiredMixin, ListView):
    model = Service
    template_name = 'pages/home/servicios/comerciales/servicios_comerciales.html'
    context_object_name = 'pdf_list'
    paginate_by = 10

    def get_queryset(self):
        return Service.objects.filter(service_type=Service.COMMERCIAL, target_customer__user=self.request.user).order_by('date')  # Ordenar por fecha

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Servicios Comerciales'
        context['parent'] = 'servicios'
        context['segment'] = 'comerciales'
        return context
