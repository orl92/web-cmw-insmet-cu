from django.core.management.base import BaseCommand

from apps.dashboard.models import Province, Station, Town


class Command(BaseCommand):
    help = 'Agrega municipios y estaciones de la provincia Camagüey'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tipo',
            type=str,
            choices=['municipios', 'estaciones', 'todo'],
            default='todo',
            help='Tipo de datos a agregar (municipios, estaciones, todo)'
        )

        parser.add_argument(
            '--provincia',
            type=str,
            default='Camagüey',
            help='Nombre de la provincia (por defecto: Camagüey)'
        )

    def handle(self, *args, **options):
        tipo = options['tipo']
        provincia_nombre = options['provincia']

        self.stdout.write(self.style.NOTICE(f"Iniciando proceso para provincia: {provincia_nombre}"))

        # Crear provincia Camagüey si no existe
        province, created = Province.objects.get_or_create(
            name=provincia_nombre,
            defaults={'code': '09'}
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f"Provincia creada: {provincia_nombre}"))
        else:
            self.stdout.write(self.style.WARNING(f"Provincia ya existía: {provincia_nombre}"))

        if tipo in ['municipios', 'todo']:
            self.agregar_municipios(province)

        if tipo in ['estaciones', 'todo']:
            self.agregar_estaciones(province)

        self.stdout.write(self.style.SUCCESS(f"Proceso completado para {provincia_nombre}!"))

    def agregar_municipios(self, province):
        """Agrega los municipios de Camagüey"""
        self.stdout.write(self.style.NOTICE("Agregando municipios..."))

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

        creados = 0
        existentes = 0

        # Crear los municipios
        for town_data in towns:
            town, created = Town.objects.get_or_create(
                name=town_data['name'],
                province=town_data['province'],
                defaults={
                    'latitude': town_data['latitude'],
                    'longitude': town_data['longitude']
                }
            )

            if created:
                self.stdout.write(f"  ✓ Municipio creado: {town_data['name']}")
                creados += 1
            else:
                self.stdout.write(f"  → Municipio ya existía: {town_data['name']}")
                existentes += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Municipios procesados: {creados} creados, {existentes} existentes"
            )
        )

    def agregar_estaciones(self, province):
        """Agrega las estaciones meteorológicas de Camagüey"""
        self.stdout.write(self.style.NOTICE("Agregando estaciones meteorológicas..."))

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

        creadas = 0
        existentes = 0

        for s in stations:
            station, created = Station.objects.get_or_create(
                number=s['number'],
                defaults={
                    'province': s['province'],
                    'name': s['name'],
                    'latitude': s['latitude'],
                    'longitude': s['longitude']
                }
            )

            if created:
                self.stdout.write(f"  ✓ Estación creada: {s['name']} (#{s['number']})")
                creadas += 1
            else:
                # Si ya existe, actualizar los datos (opcional)
                updated = False
                if station.name != s['name']:
                    station.name = s['name']
                    updated = True
                if abs(station.latitude - s['latitude']) > 0.0001:
                    station.latitude = s['latitude']
                    updated = True
                if abs(station.longitude - s['longitude']) > 0.0001:
                    station.longitude = s['longitude']
                    updated = True

                if updated:
                    station.save()
                    self.stdout.write(f"  ↻ Estación actualizada: {s['name']} (#{s['number']})")
                else:
                    self.stdout.write(f"  → Estación ya existía: {s['name']} (#{s['number']})")

                existentes += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Estaciones procesadas: {creadas} creadas, {existentes} existentes"
            )
        )
