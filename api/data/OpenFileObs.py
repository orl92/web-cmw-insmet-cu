from datetime import datetime

from api.data.FileObs import FileObs


class OpenFileObs:
    def __init__(self, station_number, hour):
        self.__hour = hour
        self.__station_number = station_number
        self.__filename = FileObs().filename(self.__station_number, self.__hour)
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

    def allStations(self):
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
        alls = self.allStations()
        try:
            s = {
                'day': alls[0].split()[-1][:2],
                'hour': alls[0].split()[-1][2:4],
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

        for i in range(len(alls)):
            if str(self.station_number) in alls[i]:
                if alls[i].split()[-1] == 'nil=':
                    s['sesion1'] = alls[i]
                else:
                    s['sesion1'] = alls[i]
                    s['sesion2'] = alls[i + 1]
        return s
