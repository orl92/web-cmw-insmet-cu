from django.utils import timezone
from rest_framework import status
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from api.data.GetData import GetData
from api.serializers import (ForecastSerializer, StationObservationSerializer,
                             StationSerializer)
from dashboard.models import Forecasts, Station

# Create your views here.
    
class StationObservationView(GenericAPIView):
    """
    ### Vista de Observación de Estación
    Esta vista recupera los datos de observación para una estación específica a una hora determinada.
    
    **Parámetros:**
    - `hour`: La hora para la cual se solicitan los datos de observación.
    - `station_number`: El número de la estación para la cual se solicitan los datos de observación.
    
    **Respuestas:**
    - `200 OK`: Devuelve los datos de observación.
    - `400 Bad Request`: Devuelve errores de validación.
    """
    permission_classes = [AllowAny]
    serializer_class = StationObservationSerializer

    def get(self, request, hour, station_number):
        hour_str = str(hour).zfill(2)  # Convertir a cadena y asegurar dos dígitos
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
    queryset = Forecasts.objects.all()
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

    



