from datetime import date, datetime, time, timedelta, timezone

from dateutil import tz
from numpy import *

from api.data.FM12 import FM12
from api.data.Tablas import Tablas


class Descodificador:
    def __init__(self, obs):
        self.__obs = obs
        self.__fm12 = FM12()
        self.funcion()

    @property
    def filename(self):
        return self.__filename

    @filename.setter
    def filename(self, value):
        self.__filename = value

    @property
    def obs(self):

        return self.__obs

    @property
    def sesion1(self):
        return self.obs['sesion1']

    @property
    def sesion2(self):
        return self.obs['sesion2']

    @property
    def fm12(self):
        return self.__fm12

    def funcion(self):
        self.fm12.II = self.sesion1.split()[0][:2]
        self.fm12.iii = self.sesion1.split()[0][2:]
        if 'nil=' in self.obs['sesion1']:
            pass
        else:
            # self.fm12.YY = self.obs[0].split()[-1][:2]
            # self.fm12.GG = self.obs[0].split()[-1][2:4]
            # self.fm12.iW = self.obs[0].split()[-1][-1]

            # Sesion 1
            # self.fm12.II = self.sesion1.split()[0][:2]
            # self.fm12.iii = self.sesion1.split()[0][2:]
            self.fm12.iR = self.sesion1.split()[1][0]
            self.fm12.iX = self.sesion1.split()[1][1]
            self.fm12.h = self.sesion1.split()[1][2]
            self.fm12.VV = self.sesion1.split()[1][3:]
            self.fm12.N = self.sesion1.split()[2][0]
            self.fm12.dd = self.sesion1.split()[2][1:3]
            self.fm12.ff = self.sesion1.split()[2][3:]
            self.fm12._1Sn = self.sesion1.split()[3][1]
            self.fm12.TTT = self.sesion1.split()[3][2:]
            self.fm12._2Sn = self.sesion1.split()[4][1]
            self.fm12.TdTdTd = self.sesion1.split()[4][2:]
            self.fm12._3PPPP = self.sesion1.split()[5][1:]
            self.fm12._4PPPP = self.sesion1.split()[6][1:]
            self.fm12._5a = self.sesion1.split()[7][2]
            self.fm12.ppp = self.sesion1.split()[7][2:]

            if int(self.fm12.iR) <= 1:
                self.fm12._6RRR = self.sesion1.split()[8][1:4]
                self.fm12.tR = self.sesion1.split()[8][-1]
            else:
                self.fm12._6RRR = 0
                self.fm12.tR = None

            if int(self.fm12.iX) == 1 or int(self.fm12.iX) == 4:
                if int(self.fm12.iR) >= 3:
                    self.fm12._7WW = self.sesion1.split()[8][1:3]
                    self.fm12.W1 = self.sesion1.split()[8][-2]
                    self.fm12.W2 = self.sesion1.split()[8][-1]
                else:
                    self.fm12._7WW = self.sesion1.split()[9][1:3]
                    self.fm12.W1 = self.sesion1.split()[9][-2]
                    self.fm12.W2 = self.sesion1.split()[9][-1]
            else:
                self.fm12._7WW = None
                self.fm12.W1 = None
                self.fm12.W2 = None

            if int(self.fm12.iR) >= 2:
                n = 9
                if 2 <= int(self.fm12.iX) <= 3 or 5 <= int(self.fm12.iX) <= 6:
                    n = 8
            else:
                n = 10

            try:
                self.fm12._8Nh = self.sesion1.split()[n][1]
                self.fm12.CL = self.sesion1.split()[n][2]
                self.fm12.CM = self.sesion1.split()[n][3]
                self.fm12.CH = self.sesion1.split()[n][4]
            except Exception:
                pass

            # Sesion 2
            try:
                for i in range(len(self.sesion2.split())):
                    if self.sesion2.split()[i][:2] == '10':
                        self.fm12._1Sn_Tx = self.sesion2.split()[i][1]
                        self.fm12.TxTxTx = self.sesion2.split()[i][2:]
                    if self.sesion2.split()[i][:2] == '20':
                        self.fm12._2Sn_Tn = self.sesion2.split()[i][1]
                        self.fm12.TnTnTn = self.sesion2.split()[i][2:]
                    if self.sesion2.split()[i][0] == '7':
                        self.fm12.__7R24R24R24R24 = self.sesion2.split()[i][1:]
            except Exception:
                pass

    # Humedad relativa
    def get_rh(self):
        try:
            es = 6.112 * exp(((17.67 * self.get_temp()) / (self.get_temp() + 243.5)))
            e = 6.112 * exp(((17.67 * self.get_td()) / (self.get_td() + 243.5)))
            rh = 100 * (e / es)
            return int(round(rh))
        except Exception:
            return None

    # Número de la estación
    def get_estacion(self):
        return int(f'{self.fm12.II}{self.fm12.iii}')

    # Horario de la obserbación
    def get_horario(self):
        now = datetime.utcnow()
        h = datetime(year=now.year, month=now.month, day=int(self.obs['day']), hour=int(self.obs['hour']))
        h = h.replace(tzinfo=tz.tzutc())
        return h.astimezone(tz.gettz('America/Havana')).strftime('%I:00 %p')

    # Día de la obserbación
    def get_dia(self):
        now = datetime.utcnow()
        d = datetime(year=now.year, month=now.month, day=int(self.obs['day']), hour=int(self.obs['hour']))
        d = d.replace(tzinfo=tz.tzutc())
        return d.astimezone(tz.gettz('America/Havana')).strftime('%d/%m/%Y')

    # Temperatura
    def get_temp(self):
        try:
            if int(self.fm12._1Sn) == 0:
                return int(self.fm12.TTT) / 10
            elif int(self.fm12._1Sn) == 1:
                return (int(self.fm12.TTT) / 10) * -1
        except Exception:
            return None

    # Temperatura de punto de rocio
    def get_td(self):
        try:
            if int(self.fm12._2Sn) == 0:
                return int(self.fm12.TdTdTd) / 10
            elif int(self.fm12._2Sn) == 1:
                return (int(self.fm12.TdTdTd) / 10) * -1
        except Exception:
            return None

    # Direccion del viento
    def get_ddViento(self):
        try:
            return Tablas().dd[self.fm12.dd]
        except Exception:
            return None

    def get_ddViento2(self):
        try:
            return Tablas().dd2[self.fm12.dd]
        except Exception:
            return None

    # Velicidad del viento
    def get_ffViento(self):
        try:
            return f'{int(self.fm12.ff)}'
        except Exception:
            return None

    # Precipitación en la obserbación
    def get_precipitacion(self):
        try:
            if self.fm12._6RRR == '990':
                return 'Traza'
            else:
                if self.fm12._6RRR[:2] == '99':
                    return float(self.fm12._6RRR[-1]) / 10
                else:
                    return float(self.fm12._6RRR) / 10
        except Exception:
            return 0.0

    # Temperatura Maxima
    def get_tempTx(self):
        try:
            if self.fm12.TxTxTx.isdigit():
                if int(self.fm12._1Sn_Tx) == 0:
                    return float(self.fm12.TxTxTx) / 10
                elif int(self.fm12._1Sn_Tx) == 1:
                    return (float(self.fm12.TxTxTx) / 10) * -1
            else:
                return None
        except Exception:
            return None

    # Temperatura Mnima
    def get_tempTn(self):
        try:
            if self.fm12.TnTnTn.isdigit():
                if int(self.fm12._2Sn_Tn) == 0:
                    return float(self.fm12.TnTnTn) / 10
                elif int(self.fm12._2Sn_Tn) == 1:
                    return (float(self.fm12.TnTnTn) / 10) * -1
            else:
                return None
        except Exception:
            return None

    # Lluvia en 24h
    def get_precipitacion24(self):
        try:
            if self.fm12._7R24R24R24R24 == '9999':
                return 'traza'
            else:
                return float(self.fm12._7R24R24R24R24) / 10
        except Exception:
            return 0.0

    # Total de cielo cubierto
    def get_estado_cielo(self):
        try:
            if self.fm12._8Nh == '0':
                return 'Despejado'
            if 1 <= int(self.fm12._8Nh) <= 3:
                return 'Poco nublado'
            if 4 <= int(self.fm12._8Nh) <= 5:
                return 'Parcialmente nublado'
            if 5 < int(self.fm12._8Nh):
                return 'Nublado'

        except Exception:
            return None

    def get_cielo_cubierto(self):
        try:
            return int(self.fm12._8Nh)
        except Exception:
            return None
