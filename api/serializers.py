from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from common.utils import get_moon_img_path, get_sun_img_path
from dashboard.models import (
    EarlyWarning,
    ForecastExtendedDay,
    ForecastRegions,
    Forecasts,
    ScientificPublication,
    Service,
    Station,
    StormWarning,
    TropicalCyclone,
    WeatherReport,
)


class StationSerializer(serializers.ModelSerializer):
    province_code = serializers.CharField(source='province.code', read_only=True)
    province_name = serializers.CharField(source='province.name', read_only=True)

    class Meta:
        model = Station
        fields = ['province_code', 'province_name', 'name', 'number', 'latitude', 'longitude']

class StationObservationSerializer(serializers.Serializer):
    hour = serializers.CharField()
    station_number = serializers.IntegerField()
    data = serializers.JSONField()

class StationObservationAllSerializer(serializers.Serializer):
    hour = serializers.CharField()
    data = serializers.JSONField()


class ForecastSerializer(serializers.ModelSerializer):
    north = serializers.SerializerMethodField()
    interior = serializers.SerializerMethodField()
    south = serializers.SerializerMethodField()
    extended_forecast = serializers.SerializerMethodField()
    astronomical_data = serializers.SerializerMethodField()

    class Meta:
        model = Forecasts
        fields = ['date', 'north', 'interior', 'south', 'extended_forecast', 'astronomical_data']

    def _region_periods(self, obj, region_name, has_sea=False):
        result = {}
        for r in obj.regions.filter(region=region_name).order_by('period_order'):
            entry = {
                'temp': r.temp,
                'weather': r.weather,
                'weather_icon': r.weather_icon,
                'wind_dir': r.wind_dir,
                'wind_speed': r.wind_speed,
            }
            if has_sea:
                entry['sea'] = r.sea_note
            result[r.period] = entry
        return result

    @extend_schema_field(serializers.JSONField)
    def get_north(self, obj):
        return self._region_periods(obj, 'north', has_sea=True)

    @extend_schema_field(serializers.JSONField)
    def get_interior(self, obj):
        return self._region_periods(obj, 'interior')

    @extend_schema_field(serializers.JSONField)
    def get_south(self, obj):
        return self._region_periods(obj, 'south', has_sea=True)

    @extend_schema_field(serializers.JSONField)
    def get_extended_forecast(self, obj):
        return {
            f'day{d.day_number}': {
                'date': d.date,
                'min_temp': d.min_temp,
                'max_temp': d.max_temp,
                'weather': d.weather,
                'weather_icon': d.weather_icon,
            }
            for d in obj.extended_days.order_by('day_number').all()
        }

    @extend_schema_field(serializers.JSONField)
    def get_astronomical_data(self, obj):
        return {
            "lp": obj.lp,
            "lp_icon": get_moon_img_path(obj.lp),
            "nlp": obj.nlp,
            "nlp_icon": get_moon_img_path(obj.nlp),
            "nlpd": obj.nlpd,
            "sunrise": obj.sunrise,
            "sunrise_icon": get_sun_img_path('sunrise'),
            "sunset": obj.sunset,
            "sunset_icon": get_sun_img_path('sunset'),
            "uv_index": obj.uv_index
        }


class EarlyWarningSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = EarlyWarning
        fields = ['uuid', 'date', 'valid_until', 'summary', 'user']


class TropicalCycloneSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = TropicalCyclone
        fields = ['uuid', 'date', 'valid_until', 'summary', 'user']


class StormWarningSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = StormWarning
        fields = ['uuid', 'date', 'valid_until', 'summary', 'user']


class WeatherReportSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = WeatherReport
        fields = ['uuid', 'report_type', 'date', 'summary', 'user']


class ScientificPublicationSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source='author.__str__', read_only=True)
    coauthors = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = ScientificPublication
        fields = ['uuid', 'title', 'summary', 'publication_date', 'author', 'coauthors']


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['uuid', 'title', 'summary', 'service_type', 'price', 'code']
