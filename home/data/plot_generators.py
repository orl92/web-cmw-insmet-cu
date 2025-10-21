import numpy as np
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from django.conf import settings
import os
from .plot_config import get_plot_config
from django.http import JsonResponse
import base64
from io import BytesIO
import logging
import metpy.calc as mpcalc
from metpy.plots import SkewT, Hodograph
from metpy.units import units

logger = logging.getLogger(__name__)


def generate_meteo_plot(request):
    """Genera gráficos meteorológicos animados a partir de datos WRF"""
    if request.method == 'GET' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        temp_file = os.path.join(settings.MEDIA_ROOT, 'temp_data.npz')
        var_name = request.GET.get("var_name", "temp")

        try:
            with np.load(temp_file) as data:
                # Cargar datos básicos
                lats = data['lats']
                longs = data['longs']
                times = data['times']
                var_data = data['var_data']

                # Cargar componentes U y V si es wd10
                u_data = None
                v_data = None
                if var_name == 'wd10':
                    if 'U10' not in data or 'V10' not in data:
                        logger.error(f"Componentes U10/V10 no encontrados para wd10")
                        return JsonResponse({
                            'status': 'error',
                            'message': "Datos de viento no disponibles"
                        }, status=400)
                    u_data = data['U10']
                    v_data = data['V10']

                # Configuración de figura
                fig, ax = setup_figure(lats, longs, var_name)
                plot_config = get_plot_config(var_name)

                # Variables para mantener estado entre animaciones
                current_contour = None
                current_barbs = None
                current_contour_lines = None
                cbar = None

                def clear_plot():
                    nonlocal current_contour, current_barbs, current_contour_lines
                    if current_contour is not None:
                        if hasattr(current_contour, 'collections'):
                            for coll in current_contour.collections:
                                coll.remove()
                        current_contour = None
                    if current_barbs is not None:
                        current_barbs.remove()
                        current_barbs = None
                    if current_contour_lines is not None:
                        current_contour_lines.remove()
                        current_contour_lines = None

                def init():
                    nonlocal current_contour, current_barbs, current_contour_lines, cbar
                    clear_plot()

                    # Dibujar el primer frame
                    current_contour, current_barbs, current_contour_lines = draw_plot(
                        ax, var_name, plot_config,
                        lats, longs, var_data, times, 0,
                        u_data, v_data
                    )

                    # Configurar colorbar
                    cbar = setup_colorbar(fig, ax, current_contour, plot_config, var_name)
                    setup_axes(ax, plot_config, times[0])
                    return []

                def animate(i):
                    nonlocal current_contour, current_barbs, current_contour_lines
                    clear_plot()

                    # Dibujar frame actual
                    current_contour, current_barbs, current_contour_lines = draw_plot(
                        ax, var_name, plot_config,
                        lats, longs, var_data, times, i,
                        u_data, v_data
                    )

                    ax.set_title(f'{plot_config["label"]} - {times[i]}', pad=12, fontsize=11)
                    return []

                # Crear animación
                anim = FuncAnimation(
                    fig, animate,
                    frames=len(times),
                    init_func=init,
                    blit=False,
                    interval=500
                )

                jshtml = anim.to_jshtml()
                plt.close(fig)

                # Log de éxito apropiado
                logger.info(f"Gráfico {var_name} generado exitosamente: {len(times)} pasos temporales")
                
                return JsonResponse({
                    'status': 'success',
                    'animation_html': jshtml,
                    'time_steps': len(times),
                    'var_name': var_name,
                    'var_label': plot_config.get('label', var_name),
                    'message': f"Gráfico {var_name} generado con {len(times)} pasos temporales"
                })

        except FileNotFoundError:
            logger.error("Archivo de datos temporal no encontrado")
            return JsonResponse({
                'status': 'error',
                'message': "Datos no disponibles. Por favor, intente nuevamente."
            }, status=404)
            
        except KeyError as e:
            logger.error(f"Error en estructura de datos: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': "Error en los datos. Por favor, contacte al administrador."
            }, status=500)
            
        except Exception as e:
            logger.exception(f"Error inesperado en generate_meteo_plot: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': "Error interno del servidor al generar el gráfico."
            }, status=500)

    return JsonResponse({
        'status': 'error',
        'message': 'Método no permitido'
    }, status=405)


def setup_figure(lats, longs, var_name=None):
    """Configura la figura base para los mapas meteorológicos"""
    fig = plt.figure(figsize=(12, 8), frameon=False)

    # Configurar fondo negro para variables de nubosidad
    if var_name in ['clflo', 'clfmi', 'clfhi']:
        fig.patch.set_facecolor('black')
        plt.rcParams['savefig.facecolor'] = 'black'
        plt.rcParams['axes.facecolor'] = 'black'
        plt.rcParams['text.color'] = 'black'
        plt.rcParams['axes.labelcolor'] = 'black'
        plt.rcParams['xtick.color'] = 'black'
        plt.rcParams['ytick.color'] = 'black'

    ax = plt.axes(projection=ccrs.PlateCarree())

    # Configurar fondo del eje para variables de nubosidad
    if var_name in ['clflo', 'clfmi', 'clfhi']:
        ax.set_facecolor('white')

    # Ajustar extensión del mapa al área de los datos
    ax.set_extent([
        np.min(longs), np.max(longs),
        np.min(lats), np.max(lats)
    ], crs=ccrs.PlateCarree())

    # Configuración del mapa
    resolution = '10m'
    ax.add_feature(cfeature.LAND.with_scale(resolution), facecolor='#f5f5f5')
    ax.add_feature(cfeature.OCEAN.with_scale(resolution), facecolor='#c8e4ff')
    ax.add_feature(cfeature.COASTLINE.with_scale(resolution), linewidth=0.8)
    ax.add_feature(cfeature.BORDERS.with_scale(resolution), linestyle=':', linewidth=0.5)
    ax.add_feature(cfeature.STATES.with_scale(resolution), linewidth=0.3, edgecolor='gray')

    plt.tight_layout(pad=0)
    fig.subplots_adjust(left=0.05, right=0.9, bottom=0.05, top=0.95)

    return fig, ax


def draw_plot(ax, var_name, plot_config, lats, longs, var_data, times, frame_idx, u_data=None, v_data=None):
    """Dibuja un frame específico del gráfico meteorológico"""
    levels = plot_config.get('levels', 20)
    current_contour = None
    current_barbs = None
    current_contour_lines = None

    # Caso especial para precipitación (RAINC y RAINC3H)
    if var_name in ['RAINC', 'RAINC3H']:
        from matplotlib.colors import BoundaryNorm, ListedColormap
        cmap_custom = ListedColormap(plot_config['colors'])
        norm = BoundaryNorm(plot_config['levels'], cmap_custom.N)

        current_contour = ax.contourf(
            longs, lats, var_data[frame_idx],
            levels=plot_config['levels'],
            cmap=cmap_custom,
            norm=norm,
            extend=plot_config['extend'],
            transform=ccrs.PlateCarree()
        )

    # Caso especial para dirección del viento (wd10)
    elif var_name == 'wd10':
        current_contour = ax.contourf(
            longs, lats, var_data[frame_idx],
            cmap=plot_config['cmap'],
            levels=plot_config['levels'],
            extend=plot_config.get('extend', 'neither'),
            transform=ccrs.PlateCarree()
        )

        step = 2
        current_barbs = ax.barbs(
            longs[::step, ::step], lats[::step, ::step],
            u_data[frame_idx][::step, ::step],
            v_data[frame_idx][::step, ::step],
            length=6,
            barb_increments={'half': 2, 'full': 4, 'flag': 20},
            color=plot_config.get('barb_color', 'black'),
            transform=ccrs.PlateCarree()
        )

    # Caso para nubosidad (convertir a porcentaje)
    elif var_name in ['clflo', 'clfmi', 'clfhi']:
        current_contour = ax.contourf(
            longs, lats, var_data[frame_idx] * 100,
            levels=levels,
            cmap=plot_config['cmap'],
            vmin=plot_config.get('vmin'),
            vmax=plot_config.get('vmax'),
            extend=plot_config.get('extend', 'neither'),
            transform=ccrs.PlateCarree()
        )

    # Para todas las demás variables
    else:
        current_contour = ax.contourf(
            longs, lats, var_data[frame_idx],
            levels=levels,
            cmap=plot_config['cmap'],
            vmin=plot_config.get('vmin'),
            vmax=plot_config.get('vmax'),
            extend=plot_config.get('extend', 'neither'),
            transform=ccrs.PlateCarree()
        )

    # Añadir líneas de contorno para slp y PSFC
    if var_name in ['slp', 'PSFC']:
        current_contour_lines = ax.contour(
            longs, lats, var_data[frame_idx],
            levels=np.arange(950, 1051, 2),
            colors='black',
            linewidths=0.5,
            transform=ccrs.PlateCarree()
        )
        ax.clabel(current_contour_lines, inline=True, fontsize=8, fmt='%1.0f hPa')

    return current_contour, current_barbs, current_contour_lines


def setup_colorbar(fig, ax, contour, plot_config, var_name):
    """Configura la colorbar según el tipo de variable"""
    # Configurar colorbar para nubosidad
    if var_name in ['clflo', 'clfmi', 'clfhi']:
        cbar = fig.colorbar(
            contour, ax=ax,
            orientation='vertical',
            pad=0.02, aspect=25, shrink=0.80
        )
        cbar.ax.yaxis.set_tick_params(color='black')
        plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='black')
        cbar.outline.set_edgecolor('black')
        cbar.set_label(plot_config['units'], rotation=0, labelpad=15,
                       fontsize=9, weight='bold', color='black')
    else:
        cbar = fig.colorbar(
            contour, ax=ax,
            orientation='vertical',
            pad=0.02, aspect=25, shrink=0.80
        )
        cbar.set_label(plot_config['units'], rotation=0, labelpad=15,
                       fontsize=9, weight='bold')

    # Configuración especial para RAINC y RAINC3H
    if var_name in ['RAINC', 'RAINC3H']:
        cbar.set_ticks(plot_config['levels'])
        tick_labels = [f"{x:.1f}" if x < 1 else f"{int(x)}" for x in plot_config['levels']]
        cbar.set_ticklabels(tick_labels)
        cbar.ax.axhline(y=0.1, color='gray', linestyle='--', linewidth=0.5)

    # Configuración para nubosidad
    if var_name in ['clflo', 'clfmi', 'clfhi']:
        cbar.set_ticks(plot_config['levels'])
        cbar.set_ticklabels(plot_config['tick_labels'])

    # Configuración especial para dirección del viento (wd10)
    elif var_name == 'wd10':
        directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                      'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW', 'N']
        ticks = plot_config['levels']
        cbar.set_ticks(ticks)
        cbar.set_ticklabels(directions)

    # Configuración para otras variables con niveles definidos
    elif isinstance(plot_config.get('levels'), (list, np.ndarray)):
        cbar.set_ticks(plot_config['levels'])
        cbar.set_ticklabels([f"{x:.1f}" if isinstance(x, float) else f"{x}" for x in plot_config['levels']])

    return cbar


def setup_axes(ax, plot_config, time_str):
    """Configura los ejes y elementos del mapa"""
    ax.set_xlabel('Longitud', fontsize=9, labelpad=8)
    ax.set_ylabel('Latitud', fontsize=9, labelpad=8)

    gl = ax.gridlines(draw_labels=True, linestyle='--', alpha=0.5)
    gl.top_labels = False
    gl.right_labels = False
    gl.xlabel_style = {'size': 8}
    gl.ylabel_style = {'size': 8}

    ax.set_title(f'{plot_config["label"]} - {time_str}', pad=12, fontsize=11)


def generate_skewt(sounding_data):
    """Genera un diagrama Skew-T y Hodógrafo a partir de datos de sondeo"""
    try:
        # Validar datos de entrada
        if not sounding_data or not all(key in sounding_data for key in ['p', 'T', 'Td', 'u', 'v', 'z']):
            logger.error("Datos de sondeo incompletos o inválidos")
            raise ValueError("Datos de sondeo incompletos")

        # Extraer datos del sondeo con unidades
        p = sounding_data['p']['value'] * units(sounding_data['p']['unit'])
        T = sounding_data['T']['value'] * units(sounding_data['T']['unit'])
        Td = sounding_data['Td']['value'] * units(sounding_data['Td']['unit'])
        u = sounding_data['u']['value'] * units(sounding_data['u']['unit'])
        v = sounding_data['v']['value'] * units(sounding_data['v']['unit'])
        z = sounding_data['z']['value'] * units(sounding_data['z']['unit'])

        # Crear figura con dimensiones específicas
        fig = plt.figure(figsize=(18, 12))

        # STEP 1: CREATE THE SKEW-T OBJECT
        skew = SkewT(fig, rotation=45, rect=(0.05, 0.05, 0.50, 0.90))

        # Configuración de límites y etiquetas
        skew.ax.set_adjustable('datalim')
        skew.ax.set_ylim(1000, 100)
        skew.ax.set_xlim(-20, 30)
        skew.ax.set_xlabel(str.upper(f'Temperature ({T.units:~P})'), weight='bold')
        skew.ax.set_ylabel(str.upper(f'Pressure ({p.units:~P})'), weight='bold')

        # Fondo blanco
        fig.set_facecolor('#ffffff')
        skew.ax.set_facecolor('#ffffff')

        # Patrón de sombreado de isotermas
        x1 = np.linspace(-100, 40, 8)
        x2 = np.linspace(-90, 50, 8)
        y = [1100, 50]
        for i in range(8):
            skew.shade_area(y=y, x1=x1[i], x2=x2[i], color='gray', alpha=0.02, zorder=1)

        # STEP 2: PLOT DATA ON THE SKEW-T
        skew.plot(p, T, 'r', lw=4, label='TEMPERATURE')
        skew.plot(p, Td, 'g', lw=4, label='DEWPOINT')

        # Resample wind barbs
        interval = np.logspace(2, 3, 40) * units.hPa
        idx = mpcalc.resample_nn_1d(p, interval)
        skew.plot_barbs(pressure=p[idx], u=u[idx], v=v[idx])

        # Líneas de referencia
        skew.ax.axvline(0 * units.degC, linestyle='--', color='blue', alpha=0.3)
        skew.plot_dry_adiabats(lw=1, alpha=0.3)
        skew.plot_moist_adiabats(lw=1, alpha=0.3)
        skew.plot_mixing_lines(lw=1, alpha=0.3)

        # Cálculos de parcela
        lcl_pressure, lcl_temperature = mpcalc.lcl(p[0], T[0], Td[0])
        skew.plot(lcl_pressure, lcl_temperature, 'ko', markerfacecolor='black')
        prof = mpcalc.parcel_profile(p, T[0], Td[0]).to('degC')
        skew.plot(p, prof, 'k', linewidth=2, label='SB PARCEL PATH')

        # Áreas de CAPE y CIN
        skew.shade_cin(p, T, prof, Td, alpha=0.2, label='SBCIN')
        skew.shade_cape(p, T, prof, alpha=0.2, label='SBCAPE')

        # STEP 3: CREATE THE HODOGRAPH INSET
        hodo_ax = plt.axes((0.48, 0.45, 0.5, 0.5))
        h = Hodograph(hodo_ax, component_range=80.)

        # Configuración del hodógrafo
        h.add_grid(increment=20, ls='-', lw=1.5, alpha=0.5)
        h.add_grid(increment=10, ls='--', lw=1, alpha=0.2)
        h.ax.set_box_aspect(1)
        h.ax.set_yticklabels([])
        h.ax.set_xticklabels([])
        h.ax.set_xticks([])
        h.ax.set_yticks([])
        h.ax.set_xlabel(' ')
        h.ax.set_ylabel(' ')

        # Marcas en el hodógrafo
        for i in range(10, 120, 10):
            h.ax.annotate(str(i), (i, 0), xytext=(0, 2), textcoords='offset pixels',
                          clip_on=True, fontsize=10, weight='bold', alpha=0.3, zorder=0)
            h.ax.annotate(str(i), (0, i), xytext=(0, 2), textcoords='offset pixels',
                          clip_on=True, fontsize=10, weight='bold', alpha=0.3, zorder=0)

        # Plot hodograph
        h.plot_colormapped(u, v, c=z, linewidth=6, label='0-12km WIND')

        # Bunkers storm motion
        RM, LM, MW = mpcalc.bunkers_storm_motion(p, u, v, z)
        h.ax.text((RM[0].m + 0.5), (RM[1].m - 0.5), 'RM', weight='bold', ha='left',
                  fontsize=13, alpha=0.6)
        h.ax.text((LM[0].m + 0.5), (LM[1].m - 0.5), 'LM', weight='bold', ha='left',
                  fontsize=13, alpha=0.6)
        h.ax.text((MW[0].m + 0.5), (MW[1].m - 0.5), 'MW', weight='bold', ha='left',
                  fontsize=13, alpha=0.6)
        h.ax.arrow(0, 0, RM[0].m - 0.3, RM[1].m - 0.3, linewidth=2, color='black',
                   alpha=0.2, label='Bunkers RM Vector',
                   length_includes_head=True, head_width=2)

        # STEP 4: PARAMETERS BOX
        fig.patches.extend([plt.Rectangle((0.563, 0.05), 0.334, 0.37,
                                          edgecolor='black', facecolor='white',
                                          linewidth=1, alpha=1, transform=fig.transFigure,
                                          figure=fig)])

        # Cálculos de parámetros
        kindex = mpcalc.k_index(p, T, Td)
        total_totals = mpcalc.total_totals_index(p, T, Td)

        # Mixed layer properties
        ml_t, ml_td = mpcalc.mixed_layer(p, T, Td, depth=50 * units.hPa)
        ml_p, _, _ = mpcalc.mixed_parcel(p, T, Td, depth=50 * units.hPa)
        mlcape, mlcin = mpcalc.mixed_layer_cape_cin(p, T, Td, depth=50 * units.hPa)

        # Most unstable parcel
        mu_p, mu_t, mu_td, _ = mpcalc.most_unstable_parcel(p, T, Td, depth=50 * units.hPa)
        mucape, mucin = mpcalc.most_unstable_cape_cin(p, T, Td, depth=50 * units.hPa)

        # LCL height
        new_p = np.append(p[p > lcl_pressure], lcl_pressure)
        new_t = np.append(T[p > lcl_pressure], lcl_temperature)
        lcl_height = mpcalc.thickness_hydrostatic(new_p, new_t)

        # Surface based CAPE/CIN
        sbcape, sbcin = mpcalc.surface_based_cape_cin(p, T, Td)

        # Storm relative helicity
        (u_storm, v_storm), *_ = mpcalc.bunkers_storm_motion(p, u, v, z)
        *_, total_helicity1 = mpcalc.storm_relative_helicity(z, u, v, depth=1 * units.km,
                                                             storm_u=u_storm, storm_v=v_storm)
        *_, total_helicity3 = mpcalc.storm_relative_helicity(z, u, v, depth=3 * units.km,
                                                             storm_u=u_storm, storm_v=v_storm)
        *_, total_helicity6 = mpcalc.storm_relative_helicity(z, u, v, depth=6 * units.km,
                                                             storm_u=u_storm, storm_v=v_storm)

        # Bulk shear
        ubshr1, vbshr1 = mpcalc.bulk_shear(p, u, v, height=z, depth=1 * units.km)
        bshear1 = mpcalc.wind_speed(ubshr1, vbshr1)
        ubshr3, vbshr3 = mpcalc.bulk_shear(p, u, v, height=z, depth=3 * units.km)
        bshear3 = mpcalc.wind_speed(ubshr3, vbshr3)
        ubshr6, vbshr6 = mpcalc.bulk_shear(p, u, v, height=z, depth=6 * units.km)
        bshear6 = mpcalc.wind_speed(ubshr6, vbshr6)

        # Severe weather parameters
        sig_tor = mpcalc.significant_tornado(sbcape, lcl_height,
                                             total_helicity3, bshear3).to_base_units()
        super_comp = mpcalc.supercell_composite(mucape, total_helicity3, bshear3)

        # Thermodynamic parameters
        plt.figtext(0.58, 0.37, 'SBCAPE: ', weight='bold', fontsize=15,
                    color='black', ha='left')
        plt.figtext(0.71, 0.37, f'{sbcape:.0f~P}', weight='bold',
                    fontsize=15, color='orangered', ha='right')
        plt.figtext(0.58, 0.34, 'SBCIN: ', weight='bold',
                    fontsize=15, color='black', ha='left')
        plt.figtext(0.71, 0.34, f'{sbcin:.0f~P}', weight='bold',
                    fontsize=15, color='lightblue', ha='right')
        plt.figtext(0.58, 0.29, 'MLCAPE: ', weight='bold', fontsize=15,
                    color='black', ha='left')
        plt.figtext(0.71, 0.29, f'{mlcape:.0f~P}', weight='bold',
                    fontsize=15, color='orangered', ha='right')
        plt.figtext(0.58, 0.26, 'MLCIN: ', weight='bold', fontsize=15,
                    color='black', ha='left')
        plt.figtext(0.71, 0.26, f'{mlcin:.0f~P}', weight='bold',
                    fontsize=15, color='lightblue', ha='right')
        plt.figtext(0.58, 0.21, 'MUCAPE: ', weight='bold', fontsize=15,
                    color='black', ha='left')
        plt.figtext(0.71, 0.21, f'{mucape:.0f~P}', weight='bold',
                    fontsize=15, color='orangered', ha='right')
        plt.figtext(0.58, 0.18, 'MUCIN: ', weight='bold', fontsize=15,
                    color='black', ha='left')
        plt.figtext(0.71, 0.18, f'{mucin:.0f~P}', weight='bold',
                    fontsize=15, color='lightblue', ha='right')
        plt.figtext(0.58, 0.13, 'TT-INDEX: ', weight='bold', fontsize=15,
                    color='black', ha='left')
        plt.figtext(0.71, 0.13, f'{total_totals:.0f~P}', weight='bold',
                    fontsize=15, color='orangered', ha='right')
        plt.figtext(0.58, 0.10, 'K-INDEX: ', weight='bold', fontsize=15,
                    color='black', ha='left')
        plt.figtext(0.71, 0.10, f'{kindex:.0f~P}', weight='bold',
                    fontsize=15, color='orangered', ha='right')

        # Kinematic parameters
        plt.figtext(0.73, 0.37, '0-1km SRH: ', weight='bold', fontsize=15,
                    color='black', ha='left')
        plt.figtext(0.88, 0.37, f'{total_helicity1:.0f~P}',
                    weight='bold', fontsize=15, color='navy', ha='right')
        plt.figtext(0.73, 0.34, '0-1km SHEAR: ', weight='bold', fontsize=15,
                    color='black', ha='left')
        plt.figtext(0.88, 0.34, f'{bshear1:.0f~P}', weight='bold',
                    fontsize=15, color='blue', ha='right')
        plt.figtext(0.73, 0.29, '0-3km SRH: ', weight='bold', fontsize=15,
                    color='black', ha='left')
        plt.figtext(0.88, 0.29, f'{total_helicity3:.0f~P}',
                    weight='bold', fontsize=15, color='navy', ha='right')
        plt.figtext(0.73, 0.26, '0-3km SHEAR: ', weight='bold', fontsize=15,
                    color='black', ha='left')
        plt.figtext(0.88, 0.26, f'{bshear3:.0f~P}', weight='bold',
                    fontsize=15, color='blue', ha='right')
        plt.figtext(0.73, 0.21, '0-6km SRH: ', weight='bold', fontsize=15,
                    color='black', ha='left')
        plt.figtext(0.88, 0.21, f'{total_helicity6:.0f~P}',
                    weight='bold', fontsize=15, color='navy', ha='right')
        plt.figtext(0.73, 0.18, '0-6km SHEAR: ', weight='bold', fontsize=15,
                    color='black', ha='left')
        plt.figtext(0.88, 0.18, f'{bshear6:.0f~P}', weight='bold',
                    fontsize=15, color='blue', ha='right')
        plt.figtext(0.73, 0.13, 'SIG TORNADO: ', weight='bold', fontsize=15,
                    color='black', ha='left')
        plt.figtext(0.88, 0.13, f'{sig_tor[0]:.0f~P}', weight='bold', fontsize=15,
                    color='orangered', ha='right')
        plt.figtext(0.73, 0.10, 'SUPERCELL COMP: ', weight='bold', fontsize=15,
                    color='black', ha='left')
        plt.figtext(0.88, 0.10, f'{super_comp[0]:.0f~P}', weight='bold', fontsize=15,
                    color='orangered', ha='right')

        # Leyendas
        skew.ax.legend(loc='upper left')
        h.ax.legend(loc='upper left')

        # Título
        plt.figtext(0.45, 0.97, 'SONDEO ATMOSFÉRICO - PERFIL VERTICAL',
                    weight='bold', fontsize=20, ha='center')

        # Convertir a base64
        buf = BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', dpi=100)
        plt.close()
        
        logger.info("Skew-T generado exitosamente")
        return base64.b64encode(buf.getvalue()).decode('utf-8')

    except Exception as e:
        logger.exception(f"Error generando Skew-T: {str(e)}")
        raise