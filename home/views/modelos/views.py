from datetime import datetime

import numpy as np
import os

from dashboard.models import Town
from home.forms import MeteoDataForm, SoundingForm
from home.data.plot_generators import generate_skewt
import json
from django.http import JsonResponse
from django.views.generic import TemplateView
from home.forms import MeteogramForm
from urllib.parse import urlencode
import requests
from django.http import HttpResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from urllib.parse import urlparse, unquote
from django.conf import settings
import logging

# Configurar logger
logger = logging.getLogger(__name__)

class MapaView(TemplateView):
    template_name = 'pages/home/modelos/maps.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Establecer valores por defecto
        initial_data = {
            'datetime_init': self.get_default_datetime(),
            'var_name': 'temp'
        }
        
        context['form'] = MeteoDataForm(initial=initial_data)
        context['initial_date'] = self.get_default_date()
        context['title'] = 'Modelo de pronóstico WRF'
        context['parent'] = 'Física de la atmósfera'
        context['segment'] = 'maps'
        return context

    def get_default_datetime(self):
        """Obtener datetime_init por defecto (fecha actual a las 00:00)"""
        now = datetime.now()
        return now.strftime('%Y%m%d00')

    def get_default_date(self):
        """Obtener fecha por defecto para el datepicker"""
        now = datetime.now()
        return now.strftime('%Y-%m-%d')

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error', 
                'message': 'Datos inválidos en la solicitud'
            }, status=400)

        form = MeteoDataForm(data)

        if form.is_valid():
            api_result = self.fetch_image_urls(
                form.cleaned_data['datetime_init'],
                form.cleaned_data['var_name']
            )

            if api_result['status'] == 'error':
                # Mejorar el mensaje de error para el usuario
                error_message = self.parse_api_error(api_result['message'])
                return JsonResponse({
                    'status': 'error',
                    'message': error_message
                }, status=500)

            return JsonResponse({
                'status': 'success',
                'datetime_init': form.cleaned_data['datetime_init'],
                'var_name': form.cleaned_data['var_name'],
                'var_label': dict(MeteoDataForm.VAR_CHOICES).get(form.cleaned_data['var_name']),
                'image_urls': api_result['image_urls'],
                'simulation_date': api_result.get('simulation_date'),
                'count': api_result.get('count')
            })

        # Mejorar los errores de validación del formulario
        errors = self.format_form_errors(form.errors.get_json_data())
        return JsonResponse({
            'status': 'error',
            'message': errors
        }, status=400)

    def parse_api_error(self, error_message):
        """Parsear y mejorar los mensajes de error de la API"""
        if "404" in error_message and "Not Found" in error_message:
            return "No se encontraron datos para los parámetros seleccionados. Por favor, intente con otra fecha o variable."
        elif "ConnectionError" in error_message or "Timeout" in error_message:
            return "Error de conexión con el servidor de datos. Por favor, intente nuevamente en unos momentos."
        elif "500" in error_message:
            return "Error interno del servidor. Por favor, contacte al administrador."
        else:
            # Para otros errores, devolver un mensaje genérico sin detalles técnicos
            return "No se pudieron cargar los datos. Por favor, verifique los parámetros e intente nuevamente."

    def format_form_errors(self, errors_dict):
        """Formatear errores del formulario para mostrarlos al usuario"""
        error_messages = []
        for field, errors in errors_dict.items():
            for error in errors:
                error_messages.append(f"{field}: {error['message']}")
        return "; ".join(error_messages)

    def fetch_image_urls(self, datetime_init, var_name):
        """Obtener URLs de imágenes de la nueva API"""
        try:
            api_url = f"http://imgwrfserver.cmw.insmet.cu/simulations/?datetime_init={datetime_init}&var_name={var_name}"
            response = requests.get(api_url, timeout=30, verify=False)
            response.raise_for_status()
            data = response.json()

            if data.get('status') != 'success':
                error_msg = data.get('message', 'Error desconocido en la API')
                raise ValueError(f"API error: {error_msg}")

            return {
                'status': 'success',
                'image_urls': data.get('image_urls', []),
                'simulation_date': data.get('simulation_date'),
                'count': data.get('count', 0)
            }

        except requests.exceptions.ConnectionError:
            return {'status': 'error', 'message': 'ConnectionError: No se pudo conectar al servidor de datos'}
        except requests.exceptions.Timeout:
            return {'status': 'error', 'message': 'Timeout: La conexión con el servidor tardó demasiado'}
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return {'status': 'error', 'message': '404: No se encontraron datos para los parámetros solicitados'}
            else:
                return {'status': 'error', 'message': f'HTTPError {e.response.status_code}: Error del servidor'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}    

class MeteogramView(TemplateView):
    template_name = 'pages/home/modelos/meteogram.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Meteorama'
        context['parent'] = 'Física de la atmósfera'
        context['segment'] = 'meteogram'

        # Obtener municipio por defecto
        default_town = Town.objects.filter(
            latitude=21.391,
            longitude=-77.908
        ).first()

        initial = {
            'datetime_init': self.request.GET.get('datetime_init', f'{datetime.now().strftime("%Y%m%d")}00'),
            'town': default_town.id if default_town else None,
        }
        context['form'] = MeteogramForm(initial=initial)
        return context

    def post(self, request, *args, **kwargs):
        form = MeteogramForm(request.POST)
        if not form.is_valid():
            return JsonResponse({
                'status': 'error',
                'errors': form.errors.get_json_data()
            }, status=400)

        try:
            # Obtener el municipio seleccionado
            town = form.cleaned_data['town']

            # Construir URL usando coordenadas del municipio
            params = {
                'datetime_init': form.cleaned_data['datetime_init'],
                'lat': town.latitude,  # Usar latitud del municipio
                'long': town.longitude,  # Usar longitud del municipio
            }
            api_url = f"https://modelo.cmw.insmet.cu/api/meteogram/?{urlencode(params)}"

            response = requests.get(api_url, timeout=10, verify=False)
            response.raise_for_status()
            api_data = response.json()

            if not isinstance(api_data, dict) or 'times' not in api_data:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Estructura de datos inesperada de la API'
                }, status=500)

            return JsonResponse({
                'status': 'success',
                'data': api_data
            })

        except requests.RequestException as e:
            return JsonResponse({
                'status': 'error',
                'message': f"Error al conectar con la API: {str(e)}"
            }, status=500)

class SoundingView(TemplateView):
    template_name = 'pages/home/modelos/sounding.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Sondeos'
        context['parent'] = 'Física de la atmósfera'
        context['segment'] = 'sounding'

        # Obtener municipio por defecto (ej. usando coordenadas predeterminadas)
        default_town = Town.objects.filter(
            latitude=21.391,
            longitude=-77.908
        ).first()

        initial = {
            'datetime_init': self.request.GET.get('datetime_init', f'{datetime.now().strftime("%Y%m%d")}00'),
            'town': default_town.id if default_town else None,
            't_index': int(self.request.GET.get('t_index', 1))
        }
        context['form'] = SoundingForm(initial=initial)
        return context

    def post(self, request, *args, **kwargs):
        form = SoundingForm(request.POST)
        if not form.is_valid():
            return JsonResponse({
                'status': 'error',
                'errors': form.errors.get_json_data()
            }, status=400)

        try:
            # Obtener el municipio seleccionado
            town = form.cleaned_data['town']

            # Construir URL para la API de sondeo usando las coordenadas del municipio
            params = {
                'datetime_init': form.cleaned_data['datetime_init'],
                'lat': town.latitude,  # Usar latitud del municipio
                'long': town.longitude,  # Usar longitud del municipio
                't_index': form.cleaned_data['t_index']
            }
            api_url = f"https://modelo.cmw.insmet.cu/api/sounding/?{urlencode(params)}"

            # Obtener datos del sondeo
            response = requests.get(api_url, timeout=10, verify=False)
            response.raise_for_status()
            sounding_data = response.json()

            # Generar el gráfico Skew-T
            img_base64 = generate_skewt(sounding_data)

            return JsonResponse({
                'status': 'success',
                'plot_image': img_base64,
                'datetime': sounding_data.get('datetime'),
                'params': params
            }, content_type='application/json')

        except requests.exceptions.RequestException as e:
            return JsonResponse({
                'status': 'error',
                'message': f"Error al conectar con la API de sondeo: {str(e)}"
            }, status=500)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f"Error al generar el gráfico: {str(e)}"
            }, status=500)

class ImageProxyModeloView(View):
    """
    Vista basada en clase para proxy de imágenes que evita problemas de CORS.
    """

    # Lista blanca de dominios permitidos (opcional, para mayor seguridad)
    ALLOWED_DOMAINS = [
        'imgwrfserver.cmw.insmet.cu',
        'localhost',
        '127.0.0.1'
    ]

    def get(self, request, *args, **kwargs):
        """
        Maneja las solicitudes GET para el proxy de imágenes.
        """
        image_url = request.GET.get('image_url', '')
        image_path = request.GET.get('image_path', '')

        # Determinar la URL de destino
        target_url = self._get_target_url(image_url, image_path)

        if not target_url:
            return HttpResponse('URL de imagen no proporcionada', status=400)

        try:
            # Validar la URL
            if not self._is_valid_url(target_url):
                return HttpResponse('URL no válida', status=400)

            # Descargar la imagen
            response = self._fetch_image(target_url)

            if response.status_code != 200:
                return HttpResponse('Error al obtener la imagen', status=response.status_code)

            # Crear la respuesta
            django_response = HttpResponse(
                response.content,
                content_type=response.headers.get('Content-Type', 'image/jpeg')
            )

            # Configurar headers para caching (opcional)
            django_response['Cache-Control'] = 'public, max-age=3600'  # Cache de 1 hora

            return django_response

        except requests.exceptions.RequestException as e:
            logger.error(f"Error en proxy de imagen: {str(e)}")
            return HttpResponse('Error al obtener la imagen', status=500)
        except Exception as e:
            logger.error(f"Error inesperado en proxy de imagen: {str(e)}")
            return HttpResponse('Error interno del servidor', status=500)

    def _get_target_url(self, image_url, image_path):
        """
        Construye la URL de destino basándose en los parámetros proporcionados.
        """
        if image_url:
            return unquote(image_url)
        elif image_path:
            # Si se proporciona image_path, construir la URL completa
            base_url = getattr(settings, 'IMAGE_SERVER_BASE_URL', 'http://imgwrfserver.cmw.insmet.cu')
            return f"{base_url}{unquote(image_path)}"
        return None

    def _is_valid_url(self, url):
        """
        Valida que la URL sea segura y esté permitida.
        """
        try:
            parsed_url = urlparse(url)

            # Verificar el esquema
            if parsed_url.scheme not in ('http', 'https'):
                return False

            # Verificar el dominio (si se ha configurado una lista blanca)
            if self.ALLOWED_DOMAINS and parsed_url.netloc not in self.ALLOWED_DOMAINS:
                return False

            return True

        except Exception:
            return False

    def _fetch_image(self, url):
        """
        Descarga la imagen desde la URL proporcionada.
        """
        headers = {
            'User-Agent': 'MeteoApp/1.0'
        }

        # Agregar headers de autenticación si es necesario
        auth_headers = self._get_auth_headers()
        headers.update(auth_headers)

        return requests.get(url, stream=True, timeout=30, headers=headers)

    def _get_auth_headers(self):
        """
        Devuelve headers de autenticación si es necesario.
        Puede ser sobrescrito en subclases para agregar autenticación.
        """
        return {}
