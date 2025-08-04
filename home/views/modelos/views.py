from datetime import datetime

import numpy as np

from home.forms import MeteoDataForm, SoundingForm
from home.data.data_handlers import fetch_meteo_data
from home.data.plot_generators import generate_meteo_plot, generate_skewt
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from home.forms import MeteogramForm
import requests
from urllib.parse import urlencode


@method_decorator(csrf_exempt, name='dispatch')
class MapaView(TemplateView):
    template_name = 'pages/home/modelos/maps.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = MeteoDataForm()
        context['title'] = 'Mapas'
        context['parent'] = 'modelos'
        context['segment'] = 'maps'
        return context

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        form = MeteoDataForm(data)

        if form.is_valid():
            return JsonResponse({
                'status': 'success',
                'datetime_init': form.cleaned_data['datetime_init'],
                'var_name': form.cleaned_data['var_name'],
                'var_label': dict(MeteoDataForm.VAR_CHOICES).get(form.cleaned_data['var_name'])
            })
        return JsonResponse({
            'status': 'error',
            'errors': form.errors.get_json_data()
        }, status=400)


@method_decorator(csrf_exempt, name='dispatch')
class MeteogramView(TemplateView):
    template_name = 'pages/home/modelos/meteogram.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Meteorama'
        context['parent'] = 'modelos'
        context['segment'] = 'meteogram'
        initial = {
            'datetime_init': self.request.GET.get('datetime_init', f'{datetime.now().strftime("%Y%m%d")}00'),
            'lat': float(self.request.GET.get('lat', 20.715)),
            'long': float(self.request.GET.get('long', -77.993))
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
            # Construir URL para la API externa
            params = {
                'datetime_init': form.cleaned_data['datetime_init'],
                'lat': form.cleaned_data['lat'],
                'long': form.cleaned_data['long']
            }
            api_url = f"https://modelo.cmw.insmet.cu/api/meteogram/?{urlencode(params)}"

            # Hacer la solicitud a la API externa
            response = requests.get(api_url)
            response.raise_for_status()
            api_data = response.json()

            # Verificar estructura básica de los datos
            if not isinstance(api_data, dict) or 'times' not in api_data:
                return JsonResponse({
                    'status': 'error',
                    'message': 'La API devolvió una estructura de datos inesperada'
                }, status=500)

            # Devolver los datos directamente
            return JsonResponse(api_data)

        except requests.RequestException as e:
            return JsonResponse({
                'status': 'error',
                'message': f"Error al conectar con la API externa: {str(e)}"
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class SoundingView(TemplateView):
    template_name = 'pages/home/modelos/sounding.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Sondeos'
        context['parent'] = 'modelos'
        context['segment'] = 'sounding'
        initial = {
            'datetime_init': self.request.GET.get('datetime_init', f'{datetime.now().strftime("%Y%m%d")}00'),
            'lat': float(self.request.GET.get('lat', 21.391)),
            'long': float(self.request.GET.get('long', -77.908)),
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
            # Construir URL para la API de sondeo
            params = {
                'datetime_init': form.cleaned_data['datetime_init'],
                'lat': form.cleaned_data['lat'],
                'long': form.cleaned_data['long'],
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


def fetch_data(request):
    return fetch_meteo_data(request)


def generate_plot(request):
    return generate_meteo_plot(request)
