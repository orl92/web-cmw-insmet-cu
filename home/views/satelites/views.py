from urllib.parse import urlparse
import requests
from django.http import HttpResponse
from django.views import View
from django.views.generic import TemplateView
import urllib.parse
import socket

# Create your views here.

class SateliteView(TemplateView):
    template_name = 'pages/home/satelites/satelites.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Mapas Satelitales'
        context['parent'] = 'imágenes'
        context['segment'] = 'satelitales'
        return context

class ProxyImageView(View):
    ALLOWED_BASE_URL = "https://tropic.ssec.wisc.edu/"
    ALLOWED_PATHS = [
        'real-time/sal/g16split/g16split.jpg',
        'real-time/sal/g16natcol/g16nc.jpg',
        'real-time/sal/g16wvupper/g16wvupper.jpg',
        'real-time/sal/g16wvmid/g16wvmid.jpg',
        'real-time/sal/g16wvlow/g16wvlow.jpg'
    ]

    def get(self, request, *args, **kwargs):
        # Obtener y validar parámetro
        image_path = request.GET.get('image_path')
        if not image_path:
            return HttpResponseForbidden("Parámetro requerido")
        
        # Normalizar y verificar ruta
        if image_path.startswith('/'):
            image_path = image_path[1:]
        
        if image_path not in self.ALLOWED_PATHS:
            return HttpResponseForbidden("Ruta no permitida")
        
        # Construir URL de forma segura
        full_url = f"{self.ALLOWED_BASE_URL}{image_path}"
        
        try:
            # Configurar seguridad adicional
            response = requests.get(
                full_url,
                stream=True,
                timeout=10,
                allow_redirects=False
            )
            
            # Validar respuesta
            if response.status_code != 200:
                return HttpResponse("Error en recurso remoto", status=502)
                
            content_type = response.headers.get('Content-Type', '')
            if not content_type.startswith('image/'):
                return HttpResponseForbidden("Tipo de contenido no válido")
                
            return HttpResponse(response.content, content_type=content_type)
            
        except requests.exceptions.RequestException:
            return HttpResponse("Error al conectar", status=502)
