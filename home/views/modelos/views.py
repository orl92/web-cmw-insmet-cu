from datetime import datetime

import numpy as np
import os

from dashboard.models import Town
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
from django.conf import settings


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
            # Obtener datos de la API externa
            api_result = self.fetch_external_api_data(
                form.cleaned_data['datetime_init'],
                form.cleaned_data['var_name']
            )

            if api_result['status'] == 'error':
                return JsonResponse({
                    'status': 'error',
                    'message': api_result['message']
                }, status=500)

            # Generar la animación en el backend
            plot_result = self.generate_plot(
                form.cleaned_data['var_name']
            )

            if plot_result['status'] == 'error':
                return JsonResponse({
                    'status': 'error',
                    'message': plot_result['message']
                }, status=500)

            return JsonResponse({
                'status': 'success',
                'datetime_init': form.cleaned_data['datetime_init'],
                'var_name': form.cleaned_data['var_name'],
                'var_label': dict(MeteoDataForm.VAR_CHOICES).get(form.cleaned_data['var_name']),
                'animation_html': plot_result['animation_html']
            })

        return JsonResponse({
            'status': 'error',
            'errors': form.errors.get_json_data()
        }, status=400)

    def fetch_external_api_data(self, datetime_init, var_name):
        """Obtener datos de la API externa"""
        try:
            api_url = f"https://modelo.cmw.insmet.cu/api/data/?datetime_init={datetime_init}&var_name={var_name}"
            response = requests.get(api_url, timeout=30, verify=False)
            response.raise_for_status()
            data = response.json()

            # Procesar datos básicos
            lats = np.array(data['lats'])
            longs = np.array(data['longs'])
            times = data['times']
            var_data = np.array(data['var'])

            # Validación de dimensiones
            if lats.shape != (29, 39) or longs.shape != (29, 39):
                raise ValueError("Dimensiones de coordenadas incorrectas, esperado (29, 39)")

            if var_data.ndim != 3 or var_data.shape[1:] != (29, 39):
                raise ValueError(
                    f"Dimensiones de variable incorrectas, esperado (t, 29, 39), recibido {var_data.shape}")

            if len(times) != var_data.shape[0]:
                raise ValueError(
                    f"Número de tiempos ({len(times)}) no coincide con primera dimensión de datos ({var_data.shape[0]})")

            # Preparar datos para guardar
            save_data = {
                'lats': lats,
                'longs': longs,
                'times': times,
                'var_data': var_data
            }

            # Manejo especial para wd10 (dirección del viento)
            if var_name == 'wd10':
                if 'U10' not in data or 'V10' not in data:
                    raise ValueError("Componentes U10 y V10 requeridos para wd10")

                u_data = np.array(data['U10'])
                v_data = np.array(data['V10'])

                # Validar dimensiones de U10 y V10
                if u_data.shape != var_data.shape:
                    raise ValueError(
                        f"Dimensiones U10 no coinciden: esperado {var_data.shape}, recibido {u_data.shape}")
                if v_data.shape != var_data.shape:
                    raise ValueError(
                        f"Dimensiones V10 no coinciden: esperado {var_data.shape}, recibido {v_data.shape}")

                save_data['U10'] = u_data
                save_data['V10'] = v_data

            # Guardar datos temporalmente
            temp_file = os.path.join(settings.MEDIA_ROOT, 'temp_data.npz')
            np.savez(temp_file, **save_data)

            return {'status': 'success'}

        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def generate_plot(self, var_name):
        """Generar la animación en el backend"""
        try:
            from home.data.plot_generators import generate_meteo_plot

            # Crear una request simulada para generate_meteo_plot
            from django.test import RequestFactory
            factory = RequestFactory()
            fake_request = factory.get(f'/fake-path/?var_name={var_name}')
            fake_request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'

            # Generar el plot
            try:
                response = generate_meteo_plot(fake_request)
            except Exception as e:
                raise e

            if hasattr(response, 'content'):
                data = json.loads(response.content)
                return data
            else:
                return {'status': 'error', 'message': 'Error generating plot'}

        except Exception as e:
            return {'status': 'error', 'message': str(e)}

@method_decorator(csrf_exempt, name='dispatch')
class MeteogramView(TemplateView):
    template_name = 'pages/home/modelos/meteogram.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Meteorama'
        context['parent'] = 'modelos'
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

@method_decorator(csrf_exempt, name='dispatch')
class SoundingView(TemplateView):
    template_name = 'pages/home/modelos/sounding.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Sondeos'
        context['parent'] = 'modelos'
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
