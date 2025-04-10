import requests
from django.http import HttpResponse
from django.views import View
from django.views.generic import TemplateView

# Create your views here.

class SateliteView(TemplateView):
    template_name = 'pages/home/satelites/satelites.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Mapas Satelitales'
        context['parent'] = 'imágenes'
        context['segment'] = 'satelitales'
        return context

import urllib.parse

class ProxyImageView(View):
    ALLOWED_DOMAINS = ['tropic.ssec.wisc.edu', '']

    def get(self, request, *args, **kwargs):
        image_url = request.GET.get('image_url')
        if image_url:
            parsed_url = urllib.parse.urlparse(image_url)
            if parsed_url.netloc in self.ALLOWED_DOMAINS:
                response = requests.get(image_url, stream=True)
                if response.status_code == 200:
                    return HttpResponse(response.content, content_type=response.headers['Content-Type'])
            return HttpResponse('Error: Dominio no permitido', status=400)
        return HttpResponse('Error: No se pudo obtener la imagen', status=400)
