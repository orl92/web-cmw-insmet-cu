from django.test import TestCase

from apps.core.templatetags import meteo_filters

WEATHER_EXPECTED = {
    'PN': 'Poco nublado',
    'PARCN': 'Parcialmente nublado',
    'N': 'Nublado',
    'AIS CHUB': 'Aislados chubascos',
    'ALG CHUB': 'Algunos chubascos',
    'NUM CHUB': 'Numerosos chubascos',
    'ALG TORM': 'Algunas tormentas',
    'NUM TORM': 'Numerosas tormentas',
}


class WeatherDescriptionTest(TestCase):
    def test_codes_map_to_spanish_names(self):
        for code, description in WEATHER_EXPECTED.items():
            with self.subTest(code=code):
                self.assertEqual(meteo_filters.weather_description(code), description)

    def test_unknown_code_returns_raw(self):
        self.assertEqual(meteo_filters.weather_description('DESCONOCIDO'), 'DESCONOCIDO')


class WeatherImgTest(TestCase):
    def test_nublado_uses_base_file(self):
        self.assertEqual(
            meteo_filters.weather_img('N'),
            '/static/dist/img/weather_icon/nublado.png',
        )

    def test_user_period_applies_suffix(self):
        self.assertEqual(
            meteo_filters.weather_img('PN', 'morning'),
            '/static/dist/img/weather_icon/poco_nublado_m.png',
        )

    def test_unknown_code_falls_back_to_nublado(self):
        self.assertEqual(
            meteo_filters.weather_img('DESCONOCIDO'),
            '/static/dist/img/weather_icon/nublado.png',
        )


class MoonImgTest(TestCase):
    def test_moon_phase_maps_to_moon_face(self):
        self.assertEqual(
            meteo_filters.moon_img('Luna Nueva'),
            '/static/dist/img/moon_faces/new_moon.png',
        )

    def test_creciente_maps_to_waxing_crescent(self):
        self.assertEqual(
            meteo_filters.moon_img('Creciente'),
            '/static/dist/img/moon_faces/waxing_crescent_moon.png',
        )

    def test_menguante_maps_to_waning_crescent(self):
        self.assertEqual(
            meteo_filters.moon_img('Menguante'),
            '/static/dist/img/moon_faces/waning_crescent_moon.png',
        )


class SunImgTest(TestCase):
    def test_sun_event_maps_to_sun_asset(self):
        self.assertEqual(
            meteo_filters.sun_img('sunrise'),
            '/static/dist/img/sun/sunrise.png',
        )
        self.assertEqual(
            meteo_filters.sun_img('sunset'),
            '/static/dist/img/sun/sunset.png',
        )


class SunDescriptionTest(TestCase):
    def test_sunrise_sunset_spanish(self):
        self.assertEqual(meteo_filters.sun_description('sunrise'), 'Amanecer')
        self.assertEqual(meteo_filters.sun_description('sunset'), 'Puesta de sol')


class MoonDescriptionTest(TestCase):
    def test_phase_maps_to_spanish(self):
        self.assertEqual(meteo_filters.moon_description('Luna Llena'), 'Luna Llena')
