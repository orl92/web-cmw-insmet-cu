import datetime as dt

import pandas as pd
from django.http import JsonResponse
from django.views import View


class ExcelJSONView(View):
    def post(self, *args, **kwargs):
        excel_file = self.request.FILES['excelFile']
        df = pd.read_excel(excel_file)

        def _val(r, c):
            v = df.values[r][c]
            try:
                return int(v) if pd.notna(v) else ''
            except (ValueError, TypeError):
                return str(v) if pd.notna(v) else ''

        rows_map = {'north': 2, 'interior': 3, 'south': 4}
        periods = ['morning', 'afternoon', 'night']
        regions = []
        for region, row in rows_map.items():
            for i, period in enumerate(periods):
                regions.append({
                    'region': region,
                    'period': period,
                    'temp': _val(row, 1 + i),
                    'weather': _val(row, 4 + i),
                    'wind_dir': _val(row, 7 + i),
                    'wind_speed': _val(row, 10 + i),
                    'sea_note': _val(row, 13 + i) if region != 'interior' else '',
                })
        extended = []
        for day_row in range(8, 13):
            extended.append({
                'day_number': day_row - 7,
                'date': _val(day_row, 1),
                'min_temp': _val(day_row, 2),
                'max_temp': _val(day_row, 3),
                'weather': _val(day_row, 4),
            })
        try:
            sunset_val = df.values[16][1]
            if hasattr(sunset_val, 'strftime'):
                sunset_str = sunset_val.strftime("%H:%M")
            else:
                try:
                    sunset_str = (dt.datetime.combine(dt.date(1, 1, 1), sunset_val) + dt.timedelta(hours=12)).strftime("%H:%M")
                except Exception:
                    sunset_str = str(sunset_val)
        except Exception:
            sunset_str = ''

        data = {
            'regions': regions,
            'extended': extended,
            'date': _val(0, 1),
            'lp': _val(14, 1),
            'nlp': _val(14, 2),
            'nlpd': _val(14, 3),
            'sunrise': _val(15, 1),
            'sunset': sunset_str,
            'uv_index': _val(17, 1),
        }
        return JsonResponse(data)
