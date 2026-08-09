"""Parsing y generación del Excel de pronósticos (layout posicional).

El archivo real (PTH_CMG.xls) es una sola hoja con un layout orientado a
impresión que se detecta por las etiquetas de las celdas (no por índices
fijos). El mismo layout se usa como plantilla descargable (``.xlsx``).

Estructura de la hoja (ídices de fila/columna 0-based):

  Fila 0  : título + etiqueta "Válido" + fecha del pronóstico
  Fila 1  : cabeceras de grupo (Temperatura, Tiempo, Viento(dd), Viento(ff), Mar)
  Fila 2  : periodos (Mañana / Tarde / Noche) repetidos por cada grupo
  Filas 3-5 : regiones (Costa norte y cayos, Interior, Costa sur)

    columnas: 0=nombre de la región; 1-3=temp; 4-6=tiempo; 7-9=viento dd;
              10-12=viento ff; 13-15=mar (solo costas)

  Fila 7  : "EXTENDIDO"
  Fila 8  : cabeceras Mínima / Máxima / Tiempo
  Filas 9-13: "Dia 1".."Dia 5" (col1=fecha, col2=mín, col3=máx, col4=tiempo)

  Filas 14-18: Astronomía (Fase Lunar, Salida Sol, Puesta Sol, Indice UV)
  Columnas 8-15 a partir de la fila 14: leyenda de códigos (se ignora).
"""

import datetime
from io import BytesIO

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

REGION_NAMES = {
    'Costa norte': 'north',
    'Interior': 'interior',
    'Costa sur': 'south',
}
SEA_REGIONS = {'north', 'south'}
PERIODS = ('morning', 'afternoon', 'night')


def _to_date(value):
    if isinstance(value, datetime.datetime):
        return value.date()
    if isinstance(value, datetime.date):
        return value
    if isinstance(value, str):
        try:
            return datetime.datetime.strptime(value, '%Y-%m-%d').date()
        except ValueError:
            return None
    return None


def _to_time(value):
    if isinstance(value, datetime.time):
        return value.strftime('%H:%M')
    if isinstance(value, datetime.datetime):
        return value.strftime('%H:%M')
    if isinstance(value, str):
        value = value.strip()
        if value.lower() == 'auto' or not value:
            return ''
        try:
            return datetime.datetime.strptime(value, '%H:%M').strftime('%H:%M')
        except ValueError:
            return value
    return ''


def _num(value):
    if value is None:
        return ''
    if isinstance(value, float):
        if pd.isna(value):
            return ''
        if value.is_integer():
            return str(int(value))
    if isinstance(value, int):
        return str(value)
    return str(value)


def _clean(value):
    if value is None:
        return ''
    if isinstance(value, float) and pd.isna(value):
        return ''
    return str(value).strip()


def _region_key(cell):
    text = _clean(cell).lower()
    if not text:
        return None
    for name in REGION_NAMES:
        if name.lower() in text:
            return REGION_NAMES[name]
    return None


def _parse_sheet(df):
    rows, cols = df.shape
    if cols < 2:
        return {'empty': True}

    region_rows = {}
    extended = []
    lp = nlp = ''
    nlpd = sunrise = sunset = uv_index = ''
    valid_date = None

    for i in range(rows):
        cell0 = df.iat[i, 0]
        label = _clean(cell0).lower()

        key = _region_key(cell0)
        if key:
            region_rows[key] = i
            continue

        if label.startswith('dia '):
            day_num = None
            for token in label.split():
                if token.isnumeric():
                    day_num = int(token)
                    break
            if day_num is not None and cols >= 5:
                extended.append(
                    {
                        'day_number': day_num,
                        'date': _to_date(df.iat[i, 1]),
                        'min_temp': _num(df.iat[i, 2]),
                        'max_temp': _num(df.iat[i, 3]),
                        'weather': _clean(df.iat[i, 4]),
                    }
                )
            continue

        if 'fase lunar' in label:
            if cols > 1:
                lp = _clean(df.iat[i, 1])
            if cols > 2:
                nlp = _clean(df.iat[i, 2])
            if cols > 3:
                fases_date = _to_date(df.iat[i, 3])
                if fases_date:
                    nlpd = fases_date.isoformat()
            continue

        if 'salida sol' in label:
            if cols > 1:
                sunrise = _to_time(df.iat[i, 1])
            continue

        if 'puesta sol' in label:
            if cols > 1:
                sunset = _to_time(df.iat[i, 1])
            continue

        if 'indice uv' in label or 'índice uv' in label:
            if cols > 1:
                uv_index = _num(df.iat[i, 1])
            continue

    # Fecha del pronóstico: filas 0-2, buscar etiqueta "Válido"
    for i in range(min(3, rows)):
        for j in range(cols):
            if _clean(df.iat[i, j]).lower() == 'válido':
                for k in range(j + 1, cols):
                    fecha = _to_date(df.iat[i, k])
                    if fecha:
                        valid_date = fecha
                        break
                if valid_date:
                    break
        if valid_date:
            break

    if not region_rows:
        return {'empty': True}

    regions = []
    for key, i in region_rows.items():
        for offset, period in enumerate(PERIODS):
            regions.append(
                {
                    'region': key,
                    'period': period,
                    'temp': _num(df.iat[i, 1 + offset]) if cols > 1 else '',
                    'weather': _clean(df.iat[i, 4 + offset]) if cols > 4 else '',
                    'wind_dir': _clean(df.iat[i, 7 + offset]) if cols > 7 else '',
                    'wind_speed': _clean(df.iat[i, 10 + offset]) if cols > 10 else '',
                    'sea_note': (
                        _clean(df.iat[i, 13 + offset]) if cols > 13 and key in SEA_REGIONS else ''
                    ),
                }
            )

    extended.sort(key=lambda x: x.get('day_number') or 0)

    return {
        'date': valid_date.isoformat() if valid_date else '',
        'regions': regions,
        'extended': extended,
        'lp': lp,
        'nlp': nlp,
        'nlpd': nlpd,
        'sunrise': sunrise,
        'sunset': sunset,
        'uv_index': uv_index,
    }


def parse_excel(fileobj):
    """Lee un .xls/.xlsx de pronóstico (formato posicional) y devuelve el
    dict JSON para ``forecast.js``. En error devuelve ``{'error': str}``.
    """
    try:
        sheets = pd.read_excel(fileobj, sheet_name=None, header=None)
    except Exception as exc:  # noqa: BLE001
        return {'error': f'No se pudo leer el archivo: {exc}'}

    for df in sheets.values():
        parsed = _parse_sheet(df)
        if not parsed.get('empty'):
            return parsed

    return {'error': 'No se encontró un pronóstico válido en el archivo.'}


# ────────────────────────────────────────────────────────────────
# Plantilla descargable (.xlsx) con el mismo layout posicional
# ────────────────────────────────────────────────────────────────

GROUP_HEADERS = {
    1: 'Temperatura',
    4: 'Tiempo',
    7: 'Viento (dd)',
    10: 'Viento (ff)',
    13: 'Mar',
}
GROUP_PERIODS = {
    1: ('Mañana', 'Tarde (Máx)', 'Noche'),
    4: ('Mañana', 'Tarde', 'Noche'),
    7: ('Mañana', 'Tarde', 'Noche'),
    10: ('Mañana', 'Tarde', 'Noche'),
    13: ('Mañana', 'Tarde', 'Noche'),
}


def build_template() -> bytes:
    """Genera un .xlsx descargable con el layout del pronóstico."""
    wb = Workbook()
    ws = wb.active
    ws.title = 'Hoja1'

    thin = Side(style='thin', color='999999')
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    bold = Font(bold=True)
    center = Alignment(horizontal='center', vertical='center')
    header_fill = PatternFill('solid', fgColor='DDEBF7')

    # Fila 0: título + Válido
    ws.cell(1, 3, 'Pronóstico para CAMAGÜEY').font = Font(bold=True, size=12)
    ws.cell(1, 6, 'Válido').font = bold
    ws.cell(1, 7, '')

    # Fila 1: cabeceras de grupo
    for j, name in GROUP_HEADERS.items():
        c = ws.cell(2, j + 1, name)
        c.font = bold
        c.fill = header_fill
        c.alignment = center
        c.border = border
    for j in GROUP_PERIODS:
        ws.merge_cells(start_row=2, start_column=j, end_row=2, end_column=j + 2)
    # Fila 2: periodos
    for j, periods in GROUP_PERIODS.items():
        for off, name in enumerate(periods):
            c = ws.cell(3, j + off + 1, name)
            c.alignment = center
            c.border = border

    # Regiones: filas 4-6 (1-based) = índices 3-5, igual que el Excel real
    regions = (('Costa norte y cayos', True), ('Interior', False), ('Costa sur', True))
    for k, (name, has_sea) in enumerate(regions):
        r = 4 + k  # 1-based
        ws.cell(r, 1, name)
        for j in range(1, 16):
            if not has_sea and j >= 13:
                continue
            c = ws.cell(r, j + 1, '')
            c.border = border

    # Extendido: fila 8 'EXTENDIDO' (1-based), fila 9 cabeceras, filas 10-14 'Dia 1..5'
    ws.cell(8, 5, 'EXTENDIDO').font = bold
    for j, name in zip((2, 3, 4), ('Mínima', 'Máxima', 'Tiempo'), strict=True):
        c = ws.cell(9, j + 1, name)
        c.font = bold
        c.border = border
    for k in range(5):
        r = 10 + k
        ws.cell(r, 1, f'Dia {k + 1}')
        for j in range(1, 5):
            c = ws.cell(r, j + 1)
            c.border = border

    # Astronomía y leyenda de códigos
    ws.cell(15, 2, 'Actual').font = bold
    ws.cell(15, 3, 'Próxima').font = bold
    ws.cell(15, 9, 'Tiempos').font = bold
    ws.cell(15, 10, 'Vientos').font = bold
    ws.cell(15, 11, 'Lunas').font = bold
    ws.cell(15, 12, 'Mar').font = bold
    fill_cells = (
        (16, 'Fase Lunar'),
        (17, 'Salida Sol'),
        (18, 'Puesta Sol'),
        (19, 'Indice UV'),
    )
    for r, label in fill_cells:
        ws.cell(r, 1, label)
    for r in (16, 17, 18, 19):
        for j in (1, 2):
            ws.cell(r, j).border = border

    legend = {
        'PN': 'Poco nublado',
        'PARCN': 'Parcialmente nublado',
        'N': 'nublado',
        'AIS CHUB': 'Aislados chubascos',
        'ALG CHUB': 'Algunos chubascos',
        'NUM CHUB': 'Numerosos chubascos',
        'ALG TORM': 'Algunas tormentas',
        'NUM TORM': 'Numerosas tormentas',
        'VRB': 'Variable débil',
        'TQ': 'mar tranquila',
        'PO': 'poco oleaje',
        'O': 'oleaje',
        'MRJ': 'Marejadas',
        'FMRJ': 'Fuertes marejadas',
    }
    r = 23
    for code, desc in legend.items():
        ws.cell(r, 1, code)
        ws.cell(r, 2, desc)
        r += 1

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()
