class FM12:
    def __init__(self):
        # Día del mes TMG. Ej. O1 para el primer día, O2 para el segundo, etc. en el cual cae la hora de la observación
        self.__YY = None

        # Hora real de observación (hora UTC entera más próxima)
        self.__GG = None

        # Indicador de las unidades utilizadas para indicar ff
        # 0  Velocidad del viento estimada(m / s)
        # 1  Velocidad del viento obtenida con anemómetro(m / s)
        # 2  Velocidad del viento estimada(nudos)
        # 3  Velocidad del viento obtenida con anemómetro(nudos)
        self.__iW = None

        # Número indicativo de un bloque
        self.__II = None

        # Número indicativo de una estación
        self.__iii = None

        # Indicador para la inclusión u omisión de datos de precipitación
        # Cifra de clave | Los datos de precipitación se indican           | Grupo 6RRR tR es                                  |
        #       0        | En las secciones 1 y 3                          | Incluido en ambas secciones                       |
        #       1        | Sección 1                                       | Incluido                                          |
        #       2        | Sección 3                                       | Incluido                                          |
        #       3        | Ninguno (ni en la sección 1 ni en la sección 3) | Omitido (La cantidad de precipitación = 0)        |
        #       4        | Ninguno (ni en la sección 1 ni en la sección 3) | Omitido (No se dispone de datos de precipitación) |
        self.__iR = None

        # Tipo de explotación de la estación
        self.__iX = None

        # Altura sobre el suelo de la base de la nube más baja
        # Cifra de clave | Altura en metros | Altura en pies |
        #       0        |        0|      49|      0|       0|
        #       1        |       50|      99|      1|      50|
        #       2        |      100|     199|      2|     100|
        #       3        |      200|     299|      3|     200|
        #       4        |      300|     599|      4|     300|
        #       5        |      600|     999|      5|     600|
        #       6        |     1000|    1499|      6|    1000|
        #       7        |     1500|    1999|      7|    1500|
        #       8        |     2000|    2499|      8|    2000|
        #       9        | 2500 o más o no hay nubes| 8000 o más o no hay nubes|
        #       /        | Base de nubes desconocida, o base por debajo del nivel de la estación y las cimas por encima de la estación
        self.__h = None

        # Visibilidad horizontal en la superficie
        self.__VV = None

        # Nubosidad total (en octavos)
        self.__N = None

        # Dirección de donde sopla el viento, en decenas de grados
        self.__dd = None

        # Velocidad del viento en m/seg.
        # Nota: Todos los grupos de la sección O y los dos primeros hasta aquí definidos de la sección I se incluirán
        # siempre en las observaciones de cualquier estación sinóptica de superficie. Los grupos MiMiMjMj y YY GG Iw se
        # incluirán a manera de encabezamiento de un boletín de cifrados. SYNOP. Cuando todos los cifrados consistan en
        # datos que hubieran sido tomados a un mismo tiempo y que usen la misma unidad para cifrar la velocidad del
        # viento. La posición de la estación se indicará en cada uno de los cifrados del boletín por medio del
        # grupo II iii.
        self.__ff = None

        # 1 = Número indicador
        # Sn = Signo de la temperatura
        # Cifra de clave
        # 0   Temperatura positiva a cero
        # 1   Temperatura negativa
        self.__1Sn = None

        # Temperatura del aire en décimas de grado Celsius
        self.__TTT = None

        # 2 = Número indicador
        # Sn = Signo de la temperatura del punto de rocío
        self.__2Sn = None

        # Temperatura del punto de rocío en décimas de grado Celsius
        self.__TdTdTd = None

        # 3 = Número indicador
        # PPPP = Presión al nivel de la estación en décimas de hectopascal, omitiéndose el dígito del millar
        self.__3PPPP = None

        # 4 = Número indicador
        # PPPP = Presión al nivel del mar en décimas de hectopascal, omitiéndose el dígito del millar
        self.__4PPPP = None

        # 5 = Número indicador
        # a = Característica de la tendencia barométrica durante las tres últimas horas
        self.__5a = None

        # Tendencia barométrica al nivel de las estaciones durantes las tres últimas horas, en décimas de hectopascal
        self.__ppp = None

        # Cantidad de precipitación para período completo de 6 horas
        self.__6RRR = None

        # Duración del periodo que se refiere la cantidad de precipitación que termina a la hora a que ha sido
        # establecida en el informe.
        # Nota – Este grupo se incluirá en la Sección 1 del informe sinóptico a las horas fijas principales
        # 00, 06, 12 y 18 TMG, refiriéndose a los datos de la precipitación para periodos completos de 6 horas.
        # Y se incluirá en la Sección 3 del informe sinóptico por lo menos en las horas fijas intermedias indicando la
        # cantidad de precipitación registrada durante el periodo de 3 horas que precedió a la hora de la observación.
        self.__tR = None

        # 7 = Número indicador
        # ww = Tiempo presente
        # Nota – Este grupo se omitirá en el caso de que ni el tiempo presente ni el tiempo pasado sean significativos
        # (cifras de clave 00, 01, 02 y 03 de la tabla de cifrado WW, y 0, 1 y 2 de la tabla de cifrado W1 W2)
        # Ix indica si este grupo se ha incluido u omitido.
        # WW = Tiempo presente
        # Utilícese la cifra de clave más alta que pueda aplicarse, no obstante, la cifra 17 tiene prioridad sobre
        # las cifras 20 a 49 inclusive.
        self.__7WW = None

        # Condiciones meteorológicas pasadas
        self.__W1 = None
        self.__W2 = None

        # 8 = Número indicador
        # Nh = Cantidad de todas las nubes CL presentes o de todas las nubes CM presentes si CL = 0
        # Nota – Cuando CL y CM = 0 y CH > 0, Nh = 0 y N = Nubosidad de CH.
        self.__8Nh = None

        # Nubes bajas (Tipos): Stratocumulus, Stratus, Cumulus, Cumulonimbus
        self.__CL = None

        # Nubes medias: Alto  cumulus, Altostratus, Nimbostratus
        self.__CM = None

        # Nubes altas: Cirrus, Cirrocumulus, Cirrostratus
        self.__CH = None

        # 9 = Número indicador
        # hh = Altura de la base de la altura más baja
        self.__9hh = None

        # O = Número indicador
        # Cs = Estado del cielo en los trópicos
        self.__OCs = None

        # SÍMBOLO = DL
        # Dirección de donde se mueven las nubes bajas
        self.__DL = None

        # SÍMBOLO = DM
        # Dirección de donde se mueven las nubes medias
        self.__DM = None

        # SÍMBOLO = DH
        # Dirección de donde se mueven las nubes altas
        self.__DH = None

        # I = Número indicador
        # Sn = Signo de la temperatura máxima (tabla 9)
        self.__1Sn_Tx = None

        # Temperatura máxima del aire en décimas de grado Celsius
        # La temperatura máxima se indicará de la forma siguiente:
        # Observación de la 1 a.m. (06.00z)
        # Máxima de las últimas 24 horas
        # Observación de la 7 a.m. (12.00z)
        # Máxima del día anterior (medianoche a medianoche)
        # Observación de la 1 p.m. (18.00z)
        # Máxima de las últimas 12 horas
        # Observación de la 7 p.m. (00.00z)
        # Máxima de las últimas 12 horas
        self.__TxTxTx = '--'

        # 2 = Número indicador
        # Sn = Signo de la temperatura mínima (tabla 9)
        self.__2Sn_Tn = None

        # Temperatura mínima del aire en décimas de grado Celsius
        # La temperatura mínima se indicará de la forma siguiente:
        # Observación de la 1 a.m. (06.00z)
        # Mínima de las últimas 24 horas
        # Observación de la 7 a.m. (12.00z)
        # Mínima de las últimas 12 horas
        # Observación de la 1 p.m. (18.00z)
        # Mínima de las últimas 24 horas
        # Observación de la 7 p.m. (00.00z)
        # Mínima de las últimas 18 horas
        self.__TnTnTn = '--'

        # Lluvia en 24h
        self.__7R24R24R24R24 = None
        

    @property
    def YY(self):
        return self.__YY

    @YY.setter
    def YY(self, value):
        self.__YY = value

    @property
    def GG(self):
        return self.__GG

    @GG.setter
    def GG(self, value):
        self.__GG = value

    @property
    def iW(self):
        return self.__iW

    @iW.setter
    def iW(self, value):
        self.__iW = value

    @property
    def II(self):
        return self.__II

    @II.setter
    def II(self, value):
        self.__II = value

    @property
    def iii(self):
        return self.__iii

    @iii.setter
    def iii(self, value):
        self.__iii = value

    @property
    def iR(self):
        return self.__iR

    @iR.setter
    def iR(self, value):
        self.__iR = value

    @property
    def iX(self):
        return self.__iX

    @iX.setter
    def iX(self, value):
        self.__iX = value

    @property
    def h(self):
        return self.__h

    @h.setter
    def h(self, value):
        self.__h = value

    @property
    def VV(self):
        return self.__VV

    @VV.setter
    def VV(self, value):
        self.__VV = value

    @property
    def N(self):
        return self.__N

    @N.setter
    def N(self, value):
        self.__N = value

    @property
    def dd(self):
        return self.__dd

    @dd.setter
    def dd(self, value):
        self.__dd = value

    @property
    def ff(self):
        return self.__ff

    @ff.setter
    def ff(self, value):
        self.__ff = value

    @property
    def _1Sn(self):
        return self.__1Sn

    @_1Sn.setter
    def _1Sn(self, value):
        self.__1Sn = value

    @property
    def TTT(self):
        return self.__TTT

    @TTT.setter
    def TTT(self, value):
        self.__TTT = value

    @property
    def _2Sn(self):
        return self.__2Sn

    @_2Sn.setter
    def _2Sn(self, value):
        self.__2Sn = value

    @property
    def TdTdTd(self):
        return self.__TdTdTd

    @TdTdTd.setter
    def TdTdTd(self, value):
        self.__TdTdTd = value

    @property
    def _3PPPP(self):
        return self.__3PPPP

    @_3PPPP.setter
    def _3PPPP(self, value):
        self.__3PPPP = value

    @property
    def _4PPPP(self):
        return self.__4PPPP

    @_4PPPP.setter
    def _4PPPP(self, value):
        self.__4PPPP = value

    @property
    def _5a(self):
        return self.__5a

    @_5a.setter
    def _5a(self, value):
        self.__5a = value

    @property
    def ppp(self):
        return self.__ppp

    @ppp.setter
    def ppp(self, value):
        self.__ppp = value

    @property
    def _6RRR(self):
        return self.__6RRR

    @_6RRR.setter
    def _6RRR(self, value):
        self.__6RRR = value

    @property
    def tR(self):
        return self.__tR

    @tR.setter
    def tR(self, value):
        self.__tR = value

    @property
    def _7WW(self):
        return self.__7WW

    @_7WW.setter
    def _7WW(self, value):
        self.__7WW = value

    @property
    def W1(self):
        return self.__W1

    @W1.setter
    def W1(self, value):
        self.__W1 = value

    @property
    def W2(self):
        return self.__W2

    @W2.setter
    def W2(self, value):
        self.__W2 = value

    @property
    def _8Nh(self):
        return self.__8Nh

    @_8Nh.setter
    def _8Nh(self, value):
        self.__8Nh = value

    @property
    def CL(self):
        return self.__CL

    @CL.setter
    def CL(self, value):
        self.__CL = value

    @property
    def CM(self):
        return self.__CM

    @CM.setter
    def CM(self, value):
        self.__CM = value

    @property
    def CH(self):
        return self.__CH

    @CH.setter
    def CH(self, value):
        self.__CH = value

    @property
    def _1Sn_Tx(self):
        return self.__1Sn_Tx

    @_1Sn_Tx.setter
    def _1Sn_Tx(self, value):
        self.__1Sn_Tx = value

    @property
    def TxTxTx(self):
        return self.__TxTxTx

    @TxTxTx.setter
    def TxTxTx(self, value):
        self.__TxTxTx = value

    @property
    def _2Sn_Tn(self):
        return self.__2Sn_Tn

    @_2Sn_Tn.setter
    def _2Sn_Tn(self, value):
        self.__2Sn_Tn = value

    @property
    def TnTnTn(self):
        return self.__TnTnTn

    @TnTnTn.setter
    def TnTnTn(self, value):
        self.__TnTnTn = value

    @property
    def _7R24R24R24R24(self):
        return self.__7R24R24R24R24

    @_7R24R24R24R24.setter
    def _7R24R24R24R24(self, value):
        self.__7R24R24R24R24 = value
