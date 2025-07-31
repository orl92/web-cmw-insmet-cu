import matplotlib
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

# Definir el nuevo colormap para nubosidad
colors_cloud = [
    (0.0, '#000000'),  # 0% - negro
    (0.7, '#808080'),  # 60% - gris medio
    (0.701, '#e0b0ff'),  # 60.1% - morado claro (transición abrupta)
    (1.0, '#800080')  # 100% - morado oscuro
]
cloud_cmap = LinearSegmentedColormap.from_list('cloud_cmap', colors_cloud)

# Definir el nuevo colormap para precipitación
precip_colors = [
    # Rango azul (0-1 mm)
    (0.0, '#FFFFFF'),  # 0 mm - Blanco puro
    (0.1, '#E6F7FF'),  # 0.1 mm - Azul blanquecino
    (0.2, '#B3E6FF'),  # 0.2 mm - Azul muy claro
    (0.5, '#66C2FF'),  # 0.5 mm - Azul cielo
    (1.0, '#0080FF'),  # 1 mm - Azul intenso (fin de rango azul)

    # Transición abrupta a verde
    (1.0001, '#00CC00'),  # 2 mm - Verde puro (inicio rango verde)

    # Rango verde (2-20 mm)
    (2.0, '#00DF00'),  # 2 mm - Verde intermedio
    (5.0, '#00E600'),  # 5 mm - Verde brillante
    (10.0, '#66FF00'),  # 10 mm - Verde lima
    (15.0, '#CCFF00'),  # 15 mm - Verde amarillento
    (20.0, '#FFFF00'),  # 20 mm - Amarillo puro

    # Rango amarillo/naranja (30-75 mm)
    (30.0, '#FFCC00'),  # 30 mm - Amarillo dorado
    (50.0, '#FF9900'),  # 50 mm - Naranja medio
    (75.0, '#FF6600'),  # 75 mm - Naranja intenso

    # Rango rojo/morado (100-200 mm)
    (100.0, '#FF0000'),  # 100 mm - Rojo intenso
    (150.0, '#CC00CC'),  # 150 mm - Magenta
    (200.0, '#8B4513'),  # 200 mm - Marrón (Brown)
    ('extend', '#800080'),  # Valores >200 mm - Morado (Purple)
]

# Creación del colormap con puntos discretos
precip_norm = matplotlib.colors.Normalize(vmin=0, vmax=200)
precip_cmap = matplotlib.colors.ListedColormap(
    [x[1] for x in precip_colors],
    name='precip_cmap'
)

PLOT_CONFIGS = {
    'T2': {
        'cmap': 'jet',
        'vmin': 10,
        'vmax': 40,
        'levels': np.linspace(10, 40, 19),
        'label': 'Temperatura a 2m',
        'units': '°C',
        'description': 'Temperatura del aire a 2 metros sobre la superficie'
    },
    'rh2': {
        'cmap': 'jet_r',
        'vmin': 0,
        'vmax': 100,
        'levels': np.linspace(0, 100, 21),
        'label': 'Humedad Relativa a 2m',
        'units': '%',
        'description': 'Porcentaje de saturación de humedad en el aire a 2m'
    },
    'td2': {
        'cmap': 'jet',
        'vmin': 10,
        'vmax': 40,
        'levels': np.linspace(10, 40, 19),
        'label': 'Punto de Rocío a 2m',
        'units': '°C',
        'description': 'Temperatura a la que el aire se satura con vapor de agua'
    },
    'RAINC': {
        'cmap': precip_cmap,
        'vmin': 0,
        'vmax': 200,
        'levels': [0, 0.1, 0.2, 0.5, 1, 2, 5, 10, 15, 20, 30, 50, 75, 100, 150, 200],
        'label': 'Precipitación Acumulada',
        'units': 'mm',
        'extend': 'max',
        'extend_colors': ['#8B4513', '#800080'],  # Marrón -> Morado para valores extendidos
        'colors': [x[1] for x in precip_colors],
        'boundaries': [x[0] for x in precip_colors]  # Límites exactos
    },
    'RAINC3H': {
        'cmap': precip_cmap,
        'vmin': 0,
        'vmax': 200,
        'levels': [0, 0.1, 0.2, 0.5, 1, 2, 5, 10, 15, 20, 30, 50, 75, 100, 150, 200],
        'label': 'Precipitación 3H',
        'units': 'mm',
        'extend': 'max',
        'extend_colors': ['#8B4513', '#800080'],  # Marrón -> Morado para valores extendidos
        'colors': [x[1] for x in precip_colors],
        'boundaries': [x[0] for x in precip_colors]
    },
    'slp': {
        'cmap': 'RdGy_r',
        'vmin': 980,
        'vmax': 1030,
        'levels': np.arange(980, 1030 + 2, 2),
        'label': 'Presión a Nivel del Mar',
        'units': 'hPa',
        'description': 'Presión atmosférica reducida al nivel del mar'
    },
    'PSFC': {
        'cmap': 'Blues',
        'vmin': 980,
        'vmax': 1030,
        'levels': np.arange(980, 1030 + 2, 2),
        'label': 'Presión en Superficie',
        'units': 'hPa',
        'description': 'Presión atmosférica a nivel de superficie'
    },
    'ws10': {
        'cmap': 'BuPu',
        'vmin': 0,
        'vmax': 110,
        'levels': [0, 2, 4, 7, 11, 15, 18, 25, 36, 54, 72, 90, 110],
        'label': 'Velocidad del Viento',
        'units': 'km/h',
        'description': 'Velocidad del viento a 10m sobre la superficie',
        'extend': 'max'
    },
    'wd10': {
        'cmap': plt.get_cmap('twilight'),
        'vmin': 0,
        'vmax': 360,
        'levels': np.linspace(0, 360, 17),
        'label': 'Dirección e Intensidad del Viento',
        'units': 'grados',
        'description': 'Dirección e intensidad del viento a 10m (barbas)',
        'barb_increments': {'half': 2, 'full': 4, 'flag': 20},
        'barb_density': 8,
        'barb_color': 'w'
    },
    'clflo': {
        'cmap': cloud_cmap,
        'vmin': 0,
        'vmax': 100,
        'levels': np.arange(0, 101, 5),  # Paso de 5%
        'label': 'Nubosidad Baja',
        'units': '%',
        'description': 'Fracción de cielo cubierto por nubes bajas',
        'scale_factor': 100,
        'tick_labels': [f"{x}%" for x in np.arange(0, 101, 5)]  # Etiquetas cada 5%
    },
    'clfmi': {
        'cmap': cloud_cmap,
        'vmin': 0,
        'vmax': 100,
        'levels': np.arange(0, 101, 5),  # Paso de 5%
        'label': 'Nubosidad Media',
        'units': '%',
        'description': 'Fracción de cielo cubierto por nubes medias',
        'scale_factor': 100,
        'tick_labels': [f"{x}%" for x in np.arange(0, 101, 5)]  # Etiquetas cada 5%
    },
    'clfhi': {
        'cmap': cloud_cmap,
        'vmin': 0,
        'vmax': 100,
        'levels': np.arange(0, 101, 5),  # Paso de 5%
        'label': 'Nubosidad Alta',
        'units': '%',
        'description': 'Fracción de cielo cubierto por nubes altas',
        'scale_factor': 100,
        'tick_labels': [f"{x}%" for x in np.arange(0, 101, 5)]  # Etiquetas cada 5%
    },
    # Modificar la configuración de MCAPE y MCIN en PLOT_CONFIGS
    'mcape': {
        'cmap': LinearSegmentedColormap.from_list('mcape_cmap', [
            (0.0, '#FFFFFF'),  # Blanco para el valor mínimo
            (0.2, '#FFFF00'),  # Amarillo
            (0.4, '#FFA500'),  # Naranja
            (0.6, '#FF4500'),  # Rojo-naranja
            (0.8, '#FF0000'),  # Rojo intenso
            (1.0, '#8B0000')  # Rojo oscuro/marrón
        ]),
        'vmin': 0,
        'vmax': 5000,
        'levels': [0, 100, 250, 500, 1000, 1500, 2000, 2500, 3000, 4000, 5000],
        'label': 'MCAPE',
        'units': 'J/kg',
        'description': 'Energía Potencial Convectiva Disponible',
        'extend': 'max'
    },
    'mcin': {
        'cmap': LinearSegmentedColormap.from_list('mcin_cmap', [
            (0.0, '#FFFFFF'),  # Blanco para el valor mínimo
            (0.2, '#E6F7FF'),  # Azul muy claro
            (0.4, '#B3E6FF'),  # Azul claro
            (0.6, '#66C2FF'),  # Azul medio
            (0.8, '#3399FF'),  # Azul
            (1.0, '#0066CC')  # Azul oscuro
        ]),
        'vmin': 0,
        'vmax': 500,
        'levels': [0, 50, 100, 150, 200, 250, 300, 400, 500],
        'label': 'MCIN',
        'units': 'J/kg',
        'description': 'Inhibición Convectiva',
        'extend': 'max'
    },
    'lcl': {
        'cmap': LinearSegmentedColormap.from_list('lcl_lluvia', [
            (0.0, '#FF4500'),  # Rojo (antes en 1.0)
            (0.2, '#FF8C00'),  # Naranja (antes en 0.8)
            (0.4, '#FFD700'),  # Amarillo (antes en 0.6)
            (0.6, '#3CB371'),  # Verde medio (antes en 0.3)
            (1.0, '#2E8B57')  # Verde oscuro (antes en 0.0)
        ]),
        'vmin': 0,
        'vmax': 2500,
        'levels': [0, 500, 1000, 1500, 2000, 2500],
        'label': 'LCL - Probabilidad de Tormentas',
        'units': 'm',
        'description': 'Altura de condensación: colores vibrantes = mayor riesgo de lluvia',
        'extend': 'max'
    },
    'lfc': {
        'cmap': LinearSegmentedColormap.from_list('lfc_lluvia', [
            (0.0, '#4B0082'),  # Índigo (antes en 1.0)
            (0.3, '#8A2BE2'),  # Violeta (antes en 0.7)
            (0.6, '#9370DB'),  # Morado medio (antes en 0.4)
            (1.0, '#1E90FF')  # Azul brillante (antes en 0.0)
        ]),
        'vmin': 0,
        'vmax': 5000,
        'levels': [0, 1500, 3000, 4000, 5000],
        'label': 'LFC - Energía para Tormentas',
        'units': 'm',
        'description': 'Altura de libre convección: morados/azules = condiciones óptimas',
        'extend': 'max'
    },
    'NOAHRES': {
        'cmap': 'RdBu_r',
        'vmin': -200,
        'vmax': 200,
        'levels': np.linspace(-200, 200, 21),
        'label': 'Balance de Energía Residual NOAH',
        'units': 'W/m²',
        'description': 'Residual del balance de energía superficial NOAH'
    },
    'SWDOWN': {
        'cmap': 'YlOrRd',
        'vmin': 0,
        'vmax': 1200,
        'levels': np.linspace(0, 1200, 13),
        'label': 'Radiación Solar Incidente',
        'units': 'W/m²',
        'description': 'Flujo descendente de onda corta en superficie'
    },
    'GLW': {
        'cmap': 'afmhot',
        'vmin': 200,
        'vmax': 500,
        'levels': np.linspace(200, 500, 13),
        'label': 'Radiación Infrarroja Incidente',
        'units': 'W/m²',
        'description': 'Flujo descendente de onda larga en superficie'
    },
    'SWNORM': {
        'cmap': 'YlOrBr',
        'vmin': 0,
        'vmax': 1200,
        'levels': np.linspace(0, 1200, 13),
        'label': 'Radiación Solar Normal',
        'units': 'W/m²',
        'description': 'Flujo de onda corta normal a la superficie'
    },
    'OLR': {
        'cmap': 'RdPu',
        'vmin': 100,
        'vmax': 350,
        'levels': np.linspace(100, 350, 11),
        'label': 'Radiación Infrarroja Saliente',
        'units': 'W/m²',
        'description': 'Flujo saliente de onda larga en el tope de la atmósfera'
    },
}


def get_plot_config(var_name):
    return PLOT_CONFIGS.get(var_name, {
        'cmap': 'viridis',
        'label': 'Variable',
        'description': 'Datos meteorológicos',
        'units': '',
        'levels': 20
    })
