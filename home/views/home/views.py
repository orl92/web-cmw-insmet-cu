from django.views.generic import TemplateView

# Create your views here.

class IndexView(TemplateView):
    template_name = 'pages/home/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Inicio'
        context['parent'] = ''
        context['segment'] = 'index'
        return context
