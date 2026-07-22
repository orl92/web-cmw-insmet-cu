import os

# Ruta absoluta a la carpeta
ruta_media_mapas = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'media', 'salida', 'mapas')

# Verificar si la carpeta ya existe
if not os.path.exists(ruta_media_mapas):
    # Crear la carpeta
    os.makedirs(ruta_media_mapas)

