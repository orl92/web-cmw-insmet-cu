from datetime import datetime

from apps.api.data.FileObs import FileObs


class OpenFileObs:
    def __init__(self, station_number, hour):
        self.__hour = hour
        self.__station_number = station_number
        fileobs = FileObs()
        self.__filename = fileobs.descargar_archivos_por_hora(self.__hour, self.__station_number)
        fileobs.limpiar_directorio_temporal()
        f = open(self.filename, 'r')
        self.__openFile = f.readlines()
        f.close()

    @property
    def hour(self):
        return self.__hour

    @property
    def station_number(self):
        return self.__station_number

    @property
    def filename(self):
        return self.__filename

    @filename.setter
    def filename(self, value):
        self.__filename = value

    def openFile(self):
        return self.__openFile

    def obs(self):
        obs = []
        x = self.openFile()  # read().strip().split('=')
        for i in range(len(x)):
            y = x[i].split()
            obs.append(y)
        return self.purge(x)

    def purge(self, list):
        list2 = []
        for i in range(len(list)):
            if list[i] != '\n':
                list2.append(list[i].strip())

        return list2

    def station(self):
        obs = self.obs()
        try:
            s = {
                'day': obs[0].split()[-1][:2],
                'hour': obs[0].split()[-1][2:4],
                'number': self.station_number,
                'sesion1': None,
                'sesion2': None,
            }
        except Exception:
            s = {
                'day': datetime.now().strftime('%d'),
                'hour': self.hour,
                'number': self.station_number,
                'sesion1': None,
                'sesion2': None,
            }

        for i in range(len(obs)):
            if str(self.station_number) in obs[i]:
                if obs[i].split()[-1] == 'nil=':
                    s['sesion1'] = obs[i]
                else:
                    s['sesion1'] = obs[i]
                    s['sesion2'] = obs[i + 1]
        return s
