from core.wsgi import *
from dashboard.models import Province, Town

# Crear provincia Camagüey si no existe
province, created = Province.objects.get_or_create(
    name='Camagüey',
    defaults={'code': '09'}
)

# Lista de municipios de Camagüey con sus coordenadas
towns = [
    {
        'province': province,
        'name': 'Camagüey',
        'latitude': 21.3786,
        'longitude': -77.9186
    },
    {
        'province': province,
        'name': 'Carlos M. de Céspedes',
        'latitude': 21.5764,
        'longitude': -78.2775
    },
    {
        'province': province,
        'name': 'Esmeralda',
        'latitude': 21.8536,
        'longitude': -78.1119
    },
    {
        'province': province,
        'name': 'Florida',
        'latitude': 21.5250,
        'longitude': -78.2250
    },
    {
        'province': province,
        'name': 'Guáimaro',
        'latitude': 21.0589,
        'longitude': -77.3458
    },
    {
        'province': province,
        'name': 'Jimaguayú',
        'latitude': 21.2667,
        'longitude': -77.8333
    },
    {
        'province': province,
        'name': 'Minas',
        'latitude': 21.4833,
        'longitude': -77.6000
    },
    {
        'province': province,
        'name': 'Najasa',
        'latitude': 21.0833,
        'longitude': -77.7500
    },
    {
        'province': province,
        'name': 'Nuevitas',
        'latitude': 21.5453,
        'longitude': -77.2644
    },
    {
        'province': province,
        'name': 'Santa Cruz del Sur',
        'latitude': 20.7167,
        'longitude': -77.9833
    },
    {
        'province': province,
        'name': 'Sibanicú',
        'latitude': 21.2353,
        'longitude': -77.5264
    },
    {
        'province': province,
        'name': 'Sierra de Cubitas',
        'latitude': 21.7333,
        'longitude': -77.7667
    },
    {
        'province': province,
        'name': 'Vertientes',
        'latitude': 21.2572,
        'longitude': -78.1478
    },
]

# Crear los municipios
for town_data in towns:
    # Usamos get_or_create para evitar duplicados
    town, created = Town.objects.get_or_create(
        name=town_data['name'],
        province=town_data['province'],
        defaults={
            'latitude': town_data['latitude'],
            'longitude': town_data['longitude']
        }
    )
    
    if created:
        print(f"Municipio creado: {town_data['name']}")
    else:
        print(f"Municipio ya existía: {town_data['name']}")

print("Proceso completado!")