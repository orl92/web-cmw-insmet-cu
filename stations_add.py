from core.wsgi import *
from dashboard.models import Province, Station

#Crear estaciones automaticamente

province = {
    'name': 'Camagüey',
    'code': '009'
}

Province.objects.create(name=province['name'], code=province['code'])

province = Province.objects.last()
stations = [
    {
        'province': province,
        'name': 'Florida',
        'number': 78350,
        'latitude': 21.5242080226931,
        'longitude': -78.22602520658981
    },
    {
        'province': province,
        'name': 'Santa Cruz',
        'number': 78351,
        'latitude': 20.737443694899678,
        'longitude': -78.00078832359691
    },
    {
        'province': province,
        'name': 'Esmeralda',
        'number': 78352,
        'latitude': 21.852114748242887,
        'longitude': -78.11834768458783
    },
    {
        'province': province,
        'name': 'Nuevitas',
        'number': 78353,
        'latitude': 21.559724753896162,
        'longitude': -77.24746046632944
    },
    {
        'province': province,
        'name': 'Palo Seco',
        'number': 78354,
        'latitude': 21.146645503868317,
        'longitude': -77.32119957621265
    },
    {
        'province': province,
        'name': 'Camagüey',
        'number': 78355,
        'latitude': 21.4227605081787,
        'longitude': -77.8498517205603
    },
]

for i in range(len(stations)):
    s = stations[i]
    Station.objects.create(
        province=s['province'],
        name=s['name'],
        number=s['number'],
        latitude=s['latitude'],
        longitude=s['longitude']
    )
