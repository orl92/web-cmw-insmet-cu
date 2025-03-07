from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from common.utils import get_img_path, get_moon_img_path, get_sun_img_path
from dashboard.models import Forecasts, Station

# serializers.py

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

    @extend_schema_field(serializers.JSONField)
    def get_north(self, obj):
        return {
            "morning": {
                "temp": obj.ntm,
                "weather": obj.nwm,
                "weather_icon": get_img_path(obj.nwm),
                "wind_dir": obj.nwddm,
                "wind_speed": obj.nwdfm,
                "sea": obj.nsm
            },
            "afternoon": {
                "temp": obj.nta,
                "weather": obj.nwa,
                "weather_icon": get_img_path(obj.nwa),
                "wind_dir": obj.nwdda,
                "wind_speed": obj.nwdfa,
                "sea": obj.nsa
            },
            "night": {
                "temp": obj.ntn,
                "weather": obj.nwn,
                "weather_icon": get_img_path(obj.nwn, is_night=True),
                "wind_dir": obj.nwddn,
                "wind_speed": obj.nwdfn,
                "sea": obj.nsn
            }
        }

    @extend_schema_field(serializers.JSONField)
    def get_interior(self, obj):
        return {
            "morning": {
                "temp": obj.itm,
                "weather": obj.iwm,
                "weather_icon": get_img_path(obj.iwm),
                "wind_dir": obj.iwddm,
                "wind_speed": obj.iwdfm
            },
            "afternoon": {
                "temp": obj.ita,
                "weather": obj.iwa,
                "weather_icon": get_img_path(obj.iwa),
                "wind_dir": obj.iwdda,
                "wind_speed": obj.iwdfa
            },
            "night": {
                "temp": obj.itn,
                "weather": obj.iwn,
                "weather_icon": get_img_path(obj.iwn, is_night=True),
                "wind_dir": obj.iwddn,
                "wind_speed": obj.iwdfn
            }
        }

    @extend_schema_field(serializers.JSONField)
    def get_south(self, obj):
        return {
            "morning": {
                "temp": obj.stm,
                "weather": obj.swm,
                "weather_icon": get_img_path(obj.swm),
                "wind_dir": obj.swddm,
                "wind_speed": obj.swdfm,
                "sea": obj.ssm
            },
            "afternoon": {
                "temp": obj.sta,
                "weather": obj.swa,
                "weather_icon": get_img_path(obj.swa),
                "wind_dir": obj.swdda,
                "wind_speed": obj.swdfa,
                "sea": obj.ssa
            },
            "night": {
                "temp": obj.stn,
                "weather": obj.swn,
                "weather_icon": get_img_path(obj.swn, is_night=True),
                "wind_dir": obj.swddn,
                "wind_speed": obj.swdfn,
                "sea": obj.ssn
            }
        }

    @extend_schema_field(serializers.JSONField)
    def get_extended_forecast(self, obj):
        return {
            "day1": {
                "date": obj.day1_date,
                "min_temp": obj.day1_min_temp,
                "max_temp": obj.day1_max_temp,
                "weather": obj.day1_weather,
                "weather_icon": get_img_path(obj.day1_weather)
            },
            "day2": {
                "date": obj.day2_date,
                "min_temp": obj.day2_min_temp,
                "max_temp": obj.day2_max_temp,
                "weather": obj.day2_weather,
                "weather_icon": get_img_path(obj.day2_weather)
            },
            "day3": {
                "date": obj.day3_date,
                "min_temp": obj.day3_min_temp,
                "max_temp": obj.day3_max_temp,
                "weather": obj.day3_weather,
                "weather_icon": get_img_path(obj.day3_weather)
            },
            "day4": {
                "date": obj.day4_date,
                "min_temp": obj.day4_min_temp,
                "max_temp": obj.day4_max_temp,
                "weather": obj.day4_weather,
                "weather_icon": get_img_path(obj.day4_weather)
            },
            "day5": {
                "date": obj.day5_date,
                "min_temp": obj.day5_min_temp,
                "max_temp": obj.day5_max_temp,
                "weather": obj.day5_weather,
                "weather_icon": get_img_path(obj.day5_weather)
            }
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