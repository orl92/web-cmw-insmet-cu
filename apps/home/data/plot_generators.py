import matplotlib
import numpy as np

matplotlib.use('Agg')
import base64
import logging
from io import BytesIO

import matplotlib.pyplot as plt
import metpy.calc as mpcalc
from metpy.plots import Hodograph, SkewT
from metpy.units import units

logger = logging.getLogger(__name__)


def generate_skewt(sounding_data):
    """Genera un diagrama Skew-T y Hodógrafo a partir de datos de sondeo"""
    try:
        # Validar datos de entrada
        if not sounding_data or not all(
            key in sounding_data for key in ['p', 'T', 'Td', 'u', 'v', 'z']
        ):
            logger.error('Datos de sondeo incompletos o inválidos')
            raise ValueError('Datos de sondeo incompletos')

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
        h = Hodograph(hodo_ax, component_range=80.0)

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
            h.ax.annotate(
                str(i),
                (i, 0),
                xytext=(0, 2),
                textcoords='offset pixels',
                clip_on=True,
                fontsize=10,
                weight='bold',
                alpha=0.3,
                zorder=0,
            )
            h.ax.annotate(
                str(i),
                (0, i),
                xytext=(0, 2),
                textcoords='offset pixels',
                clip_on=True,
                fontsize=10,
                weight='bold',
                alpha=0.3,
                zorder=0,
            )

        # Plot hodograph
        h.plot_colormapped(u, v, c=z, linewidth=6, label='0-12km WIND')

        # Bunkers storm motion
        RM, LM, MW = mpcalc.bunkers_storm_motion(p, u, v, z)
        h.ax.text(
            (RM[0].m + 0.5), (RM[1].m - 0.5), 'RM', weight='bold', ha='left', fontsize=13, alpha=0.6
        )
        h.ax.text(
            (LM[0].m + 0.5), (LM[1].m - 0.5), 'LM', weight='bold', ha='left', fontsize=13, alpha=0.6
        )
        h.ax.text(
            (MW[0].m + 0.5), (MW[1].m - 0.5), 'MW', weight='bold', ha='left', fontsize=13, alpha=0.6
        )
        h.ax.arrow(
            0,
            0,
            RM[0].m - 0.3,
            RM[1].m - 0.3,
            linewidth=2,
            color='black',
            alpha=0.2,
            label='Bunkers RM Vector',
            length_includes_head=True,
            head_width=2,
        )

        # STEP 4: PARAMETERS BOX
        fig.patches.extend(
            [
                plt.Rectangle(
                    (0.563, 0.05),
                    0.334,
                    0.37,
                    edgecolor='black',
                    facecolor='white',
                    linewidth=1,
                    alpha=1,
                    transform=fig.transFigure,
                    figure=fig,
                )
            ]
        )

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
        *_, total_helicity1 = mpcalc.storm_relative_helicity(
            z, u, v, depth=1 * units.km, storm_u=u_storm, storm_v=v_storm
        )
        *_, total_helicity3 = mpcalc.storm_relative_helicity(
            z, u, v, depth=3 * units.km, storm_u=u_storm, storm_v=v_storm
        )
        *_, total_helicity6 = mpcalc.storm_relative_helicity(
            z, u, v, depth=6 * units.km, storm_u=u_storm, storm_v=v_storm
        )

        # Bulk shear
        ubshr1, vbshr1 = mpcalc.bulk_shear(p, u, v, height=z, depth=1 * units.km)
        bshear1 = mpcalc.wind_speed(ubshr1, vbshr1)
        ubshr3, vbshr3 = mpcalc.bulk_shear(p, u, v, height=z, depth=3 * units.km)
        bshear3 = mpcalc.wind_speed(ubshr3, vbshr3)
        ubshr6, vbshr6 = mpcalc.bulk_shear(p, u, v, height=z, depth=6 * units.km)
        bshear6 = mpcalc.wind_speed(ubshr6, vbshr6)

        # Severe weather parameters
        sig_tor = mpcalc.significant_tornado(
            sbcape, lcl_height, total_helicity3, bshear3
        ).to_base_units()
        super_comp = mpcalc.supercell_composite(mucape, total_helicity3, bshear3)

        # Thermodynamic parameters
        plt.figtext(0.58, 0.37, 'SBCAPE: ', weight='bold', fontsize=15, color='black', ha='left')
        plt.figtext(
            0.71, 0.37, f'{sbcape:.0f~P}', weight='bold', fontsize=15, color='orangered', ha='right'
        )
        plt.figtext(0.58, 0.34, 'SBCIN: ', weight='bold', fontsize=15, color='black', ha='left')
        plt.figtext(
            0.71, 0.34, f'{sbcin:.0f~P}', weight='bold', fontsize=15, color='lightblue', ha='right'
        )
        plt.figtext(0.58, 0.29, 'MLCAPE: ', weight='bold', fontsize=15, color='black', ha='left')
        plt.figtext(
            0.71, 0.29, f'{mlcape:.0f~P}', weight='bold', fontsize=15, color='orangered', ha='right'
        )
        plt.figtext(0.58, 0.26, 'MLCIN: ', weight='bold', fontsize=15, color='black', ha='left')
        plt.figtext(
            0.71, 0.26, f'{mlcin:.0f~P}', weight='bold', fontsize=15, color='lightblue', ha='right'
        )
        plt.figtext(0.58, 0.21, 'MUCAPE: ', weight='bold', fontsize=15, color='black', ha='left')
        plt.figtext(
            0.71, 0.21, f'{mucape:.0f~P}', weight='bold', fontsize=15, color='orangered', ha='right'
        )
        plt.figtext(0.58, 0.18, 'MUCIN: ', weight='bold', fontsize=15, color='black', ha='left')
        plt.figtext(
            0.71, 0.18, f'{mucin:.0f~P}', weight='bold', fontsize=15, color='lightblue', ha='right'
        )
        plt.figtext(0.58, 0.13, 'TT-INDEX: ', weight='bold', fontsize=15, color='black', ha='left')
        plt.figtext(
            0.71,
            0.13,
            f'{total_totals:.0f~P}',
            weight='bold',
            fontsize=15,
            color='orangered',
            ha='right',
        )
        plt.figtext(0.58, 0.10, 'K-INDEX: ', weight='bold', fontsize=15, color='black', ha='left')
        plt.figtext(
            0.71, 0.10, f'{kindex:.0f~P}', weight='bold', fontsize=15, color='orangered', ha='right'
        )

        # Kinematic parameters
        plt.figtext(0.73, 0.37, '0-1km SRH: ', weight='bold', fontsize=15, color='black', ha='left')
        plt.figtext(
            0.88,
            0.37,
            f'{total_helicity1:.0f~P}',
            weight='bold',
            fontsize=15,
            color='navy',
            ha='right',
        )
        plt.figtext(
            0.73, 0.34, '0-1km SHEAR: ', weight='bold', fontsize=15, color='black', ha='left'
        )
        plt.figtext(
            0.88, 0.34, f'{bshear1:.0f~P}', weight='bold', fontsize=15, color='blue', ha='right'
        )
        plt.figtext(0.73, 0.29, '0-3km SRH: ', weight='bold', fontsize=15, color='black', ha='left')
        plt.figtext(
            0.88,
            0.29,
            f'{total_helicity3:.0f~P}',
            weight='bold',
            fontsize=15,
            color='navy',
            ha='right',
        )
        plt.figtext(
            0.73, 0.26, '0-3km SHEAR: ', weight='bold', fontsize=15, color='black', ha='left'
        )
        plt.figtext(
            0.88, 0.26, f'{bshear3:.0f~P}', weight='bold', fontsize=15, color='blue', ha='right'
        )
        plt.figtext(0.73, 0.21, '0-6km SRH: ', weight='bold', fontsize=15, color='black', ha='left')
        plt.figtext(
            0.88,
            0.21,
            f'{total_helicity6:.0f~P}',
            weight='bold',
            fontsize=15,
            color='navy',
            ha='right',
        )
        plt.figtext(
            0.73, 0.18, '0-6km SHEAR: ', weight='bold', fontsize=15, color='black', ha='left'
        )
        plt.figtext(
            0.88, 0.18, f'{bshear6:.0f~P}', weight='bold', fontsize=15, color='blue', ha='right'
        )
        plt.figtext(
            0.73, 0.13, 'SIG TORNADO: ', weight='bold', fontsize=15, color='black', ha='left'
        )
        plt.figtext(
            0.88,
            0.13,
            f'{sig_tor[0]:.0f~P}',
            weight='bold',
            fontsize=15,
            color='orangered',
            ha='right',
        )
        plt.figtext(
            0.73, 0.10, 'SUPERCELL COMP: ', weight='bold', fontsize=15, color='black', ha='left'
        )
        plt.figtext(
            0.88,
            0.10,
            f'{super_comp[0]:.0f~P}',
            weight='bold',
            fontsize=15,
            color='orangered',
            ha='right',
        )

        # Leyendas
        skew.ax.legend(loc='upper left')
        h.ax.legend(loc='upper left')

        # Título
        plt.figtext(
            0.45,
            0.97,
            'SONDEO ATMOSFÉRICO - PERFIL VERTICAL',
            weight='bold',
            fontsize=20,
            ha='center',
        )

        # Convertir a base64
        buf = BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', dpi=100)
        plt.close()

        logger.info('Skew-T generado exitosamente')
        return base64.b64encode(buf.getvalue()).decode('utf-8')

    except Exception as e:
        logger.exception(f'Error generando Skew-T: {str(e)}')
        raise
