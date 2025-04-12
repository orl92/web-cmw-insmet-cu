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
import socket

class ProxyImageView(View):
    ALLOWED_DOMAINS = ['tropic.ssec.wisc.edu']
    ALLOWED_IPS = ['128.104.109.100']  # Example IP address for tropic.ssec.wisc.edu

    def is_allowed_domain(self, netloc):
        try:
            ip_address = socket.gethostbyname(netloc)
            return ip_address in self.ALLOWED_IPS
        except socket.error:
            return False

    def get(self, request, *args, **kwargs):
        image_url = request.GET.get('image_url')
        if image_url:
            parsed_url = urllib.parse.urlparse(image_url)
            if parsed_url.scheme in ['http', 'https'] and self.is_allowed_domain(parsed_url.netloc):
                response = requests.get(image_url, stream=True)
                if response.status_code == 200:
                    return HttpResponse(response.content, content_type=response.headers['Content-Type'])
            return HttpResponse('Error: Dominio no permitido', status=400)
        return HttpResponse('Error: No se pudo obtener la imagen', status=400)
