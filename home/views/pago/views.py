from django.views.generic import TemplateView



# Create your views here.

class PagoView(TemplateView):
    template_name = 'pages/home/pago/pago_qr.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Pagos en linea'
        context['parent'] = 'pago'
        context['segment'] = 'pago_qr'

        return context
