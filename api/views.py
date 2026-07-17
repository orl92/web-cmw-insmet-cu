from django.utils import timezone
from rest_framework import status
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from api.data.GetData import GetData
from api.serializers import (
    EarlyWarningSerializer,
    ForecastSerializer,
    ScientificPublicationSerializer,
    ServiceSerializer,
    StationObservationSerializer,
    StationSerializer,
    StormWarningSerializer,
    TropicalCycloneSerializer,
    WeatherReportSerializer,
)
from dashboard.models import (
    EarlyWarning,
    Forecasts,
    ScientificPublication,
    Service,
    Station,
    StormWarning,
    TropicalCyclone,
    WeatherReport,
)

ALLOWED_REPORT_TYPES = {'today', 'tomorrow', 'commentary', 'note'}
    
class StationObservationView(GenericAPIView):
    """
    ### Vista de Observación de Estación Meteorológica
    Recupera datos de observación para una estación específica a una hora determinada.

    **Parámetros:**
    - `hour` (str): Hora de observación (formato HH). 
      Horas permitidas: 00, 03, 06, 09, 12, 15, 18, 21
    - `station_number` (str): Número de la estación meteorológica.
    
    **Estaciones disponibles:**
    - Florida: 78350
    - Palo Seco: 78354
    - Nuevitas: 78353
    - Esmeralda: 78352
    - Santa Cruz: 78351
    - Camagüey: 78355
    
    **Respuestas:**
    - `200 OK`: Devuelve los datos de observación.
    - `400 Bad Request`: Devuelve errores de validación.
    """
    permission_classes = [AllowAny]
    serializer_class = StationObservationSerializer

    def get(self, request, hour, station_number):
        allowed_hours = {'00', '03', '06', '09', '12', '15', '18', '21'}
        stations = {
            '78350': 'Florida',
            '78354': 'Palo Seco',
            '78353': 'Nuevitas',
            '78352': 'Esmeralda',
            '78351': 'Santa Cruz',
            '78355': 'Camagüey'
        }
        
        hour_str = str(hour).zfill(2)
        
        if hour_str not in allowed_hours:
            return Response(
                {"error": "Invalid hour parameter. Valid hours: 00, 03, 06, 09, 12, 15, 18, 21"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if str(station_number) not in stations:
            return Response(
                {"error": "Invalid station number. Available stations: " + ", ".join(f"{k} ({v})" for k, v in stations.items())},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = GetData().get_station(hour_str, station_number)
        serializer = self.get_serializer(data={'hour': hour_str, 'station_number': station_number, 'data': data})
        
        if serializer.is_valid():
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class StationListAPIView(ListAPIView):
    """
    ### Vista de Listado de Estaciones
    Esta vista proporciona una lista de todas las estaciones.
    
    **Respuestas:**
    - `200 OK`: Devuelve la lista de estaciones.
    """
    queryset = Station.objects.all()
    serializer_class = StationSerializer
    permission_classes = [AllowAny]

class ForecastAPIView(GenericAPIView):
    """
    ### Vista de API de Pronóstico
    Esta vista recupera los datos de pronóstico.
    
    **Parámetros:**
    - `date`: La fecha en formato Año-Mes-Dia (YYYY-MM-DD) para la cual se solicitan los datos de pronóstico. 
    
    **Respuestas:**
    - `200 OK`: Devuelve los datos de pronóstico.
    - `400 Bad Request`: Devuelve errores de validación.
    - `404 Not Found`: Devuelve un mensaje si los pronósticos no se han actualizado.
    """
    permission_classes = [AllowAny]
    queryset = Forecasts.objects.prefetch_related('regions', 'extended_days').all()
    serializer_class = ForecastSerializer

    def get(self, request, date=None):
        if date is None:
            date = timezone.now().date()
        else:
            date = timezone.datetime.strptime(date, '%Y-%m-%d').date()

        forecasts = self.queryset.filter(date=date).first()

        if not forecasts:
            return Response({"message": "Los pronósticos no se han actualizado."}, status=404)

        serializer = self.get_serializer(forecasts)
        return Response(serializer.data)


class EarlyWarningListAPIView(ListAPIView):
    serializer_class = EarlyWarningSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return EarlyWarning.objects.filter(valid_until__gte=timezone.now())


class TropicalCycloneListAPIView(ListAPIView):
    serializer_class = TropicalCycloneSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return TropicalCyclone.objects.filter(valid_until__gte=timezone.now())


class StormWarningListAPIView(ListAPIView):
    serializer_class = StormWarningSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return StormWarning.objects.filter(valid_until__gte=timezone.now())


class WeatherReportListAPIView(ListAPIView):
    serializer_class = WeatherReportSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        report_type = self.kwargs.get('type')
        if report_type not in ALLOWED_REPORT_TYPES:
            return WeatherReport.objects.none()
        return WeatherReport.objects.filter(type=report_type)


class ScientificPublicationListAPIView(ListAPIView):
    queryset = ScientificPublication.objects.all()
    serializer_class = ScientificPublicationSerializer
    permission_classes = [AllowAny]


class ServiceListAPIView(ListAPIView):
    queryset = Service.objects.filter(service_type='public')
    serializer_class = ServiceSerializer
    permission_classes = [AllowAny]



