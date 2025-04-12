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
    ALLOWED_IMAGE_PATHS = [
        'path/to/image1.jpg',
        'path/to/image2.jpg',
        'path/to/image3.jpg'
    ]

    def is_allowed_domain(self, netloc):
        try:
            ip_address = socket.gethostbyname(netloc)
            return ip_address in self.ALLOWED_IPS
        except socket.error:
            return False

    def get(self, request, *args, **kwargs):
        image_path = request.GET.get('image_path')
        if image_path in self.ALLOWED_IMAGE_PATHS:
            full_url = f"https://tropic.ssec.wisc.edu/{image_path}"
            response = requests.get(full_url, stream=True)
            if response.status_code == 200:
                return HttpResponse(response.content, content_type=response.headers['Content-Type'])
            return HttpResponse('Error: No se pudo obtener la imagen', status=400)
        return HttpResponse('Error: Ruta de imagen no permitida', status=400)
