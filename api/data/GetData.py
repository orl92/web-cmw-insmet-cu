from api.data.Descodificador import Descodificador
from api.data.OpenFileObs import OpenFileObs


class GetData:
    def __init__(self):
        self.__numbers_stations = [
            78310, 78315, 78318, 78322, 78324, 78325, 78328, 78333, 78344, 78345, 78348, 78349, 78351, 78355, 78358,
            78360, 78363, 78365, 78369, 78308, 78309, 78312, 78313, 78314, 78316, 78317, 78319, 78320, 78321, 78323,
            78326, 78327, 78329, 78330, 78331, 78332, 78334, 78335, 78337, 78338, 78339, 78340, 78341, 78342, 78343,
            78346, 78347, 78350, 78352, 78354, 78356, 78357, 78359, 78361, 78362, 78364, 78366, 78368, 78370, 78371,
            78372, 78373, 78374, 78375, 78376, 78377, 78378
        ]

    @property
    def _numbers_stations(self):
        return self.__numbers_stations

    def get_station(self, hour: str, station_number: int):
        try:
            obs = OpenFileObs(station_number, hour).station()
            d = Descodificador(obs)

            return {
                'estacion': int(d.get_estacion()),
                'dia': d.get_dia(),
                'hora': d.get_horario(),
                'estado del cielo': d.get_estado_cielo(),
                'cielo cubierto': d.get_cielo_cubierto(),
                'temperatura': d.get_temp(),  # °C
                'temperatura maxima': d.get_tempTx(),  # °C
                'temperatura minima': d.get_tempTn(),  # °C
                'humedad relativa': d.get_rh(),  # %'
                'velocidad del viento': float(d.get_ffViento()) * 3.6,  # Km/h
                'direccion del viento': d.get_ddViento(),
                'dd': d.get_ddViento2(),
                'precipitacion en 3 horas': d.get_precipitacion(),  # mm
                'precipitacion en 24 horas': d.get_precipitacion24(),  # mm
            }
        except Exception:
            return {
                'estacion': station_number,
                'data': None
            }
    
    def get_all_stations(self, hour):
        _dict = {}

        for i in self._numbers_stations:
            _dict[f'{i}'] = self.get_station(hour, i)
        return _dict

