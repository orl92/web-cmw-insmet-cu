import numpy as np
import os
import requests
from django.conf import settings
from django.http import JsonResponse


def fetch_meteo_data(request):
    if request.method == 'GET' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        datetime_init = request.GET.get('datetime_init')
        var_name = request.GET.get('var_name')

        # URL de la API externa
        api_url = f"https://modelo.cmw.insmet.cu/api/data/?datetime_init={datetime_init}&var_name={var_name}"

        try:
            response = requests.get(api_url, timeout=10, verify=False)
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

            return JsonResponse({
                'status': 'success',
                'times': times,
                'data_shape': var_data.shape,
                'message': f"Datos recibidos correctamente. Shape: {var_data.shape}"
            })

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)

    return JsonResponse({
        'status': 'error',
        'message': 'Método no permitido'
    }, status=405)
