import datetime as dt

import pandas as pd
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import Group, User
from django.contrib.sessions.models import Session
from django.core.exceptions import FieldError, ObjectDoesNotExist
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import redirect
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from common.utils import log_action
from dashboard.models import (
    EarlyWarning,
    Forecasts,
    SiteConfiguration,
    StormWarning,
    TropicalCyclone,
)

# Create your views here.
   
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

        # Rows: 2=north, 3=interior, 4=south
        # Cols: 1-3=temp, 4-6=weather, 7-9=wind_dir, 10-12=wind_speed, 13-15=sea
        # Extended: rows 8-12, cols 2-4 = min_temp, max_temp, weather
        rows_map = {'north': 2, 'interior': 3, 'south': 4}
        periods = ['morning', 'afternoon', 'night']
        regions = []
        for region, row in rows_map.items():
            for i, period in enumerate(periods):
                regions.append({
                    'temp': _val(row, 1 + i),
                    'weather': _val(row, 4 + i),
                    'wind_dir': _val(row, 7 + i),
                    'wind_speed': _val(row, 10 + i),
                    'sea_note': _val(row, 13 + i) if region != 'interior' else '',
                })
        extended = []
        for day_row in range(8, 13):
            extended.append({
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
            'lp': _val(14, 1),
            'nlp': _val(14, 2),
            'nlpd': _val(14, 3),
            'sunrise': _val(15, 1),
            'sunset': sunset_str,
            'uv_index': _val(17, 1),
        }
        return JsonResponse(data)


class DashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'pages/dashboard/dashboard.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Obtener el parámetro de rango de tiempo
        time_range = self.request.GET.get('range', '7d')
        
        # Determinar el número de días según el rango
        if time_range == '30d':
            days = 30
        elif time_range == '3m':
            days = 90
        else:
            days = 7
        
        # Fecha de inicio para filtrar
        start_date = timezone.now().date() - timezone.timedelta(days=days)

        context.update({
            'title': 'Dashboard',
            'parent': '',
            'segment': 'dashboard',
            'is_superuser': user.is_superuser,
            'selected_range': time_range,
        })

        # Datos meteorológicos comunes
        try:
            context['latest_forecast'] = Forecasts.objects.prefetch_related('regions', 'extended_days').latest('date')
        except ObjectDoesNotExist:
            context['latest_forecast'] = None
        
        # Pronósticos filtrados por rango de tiempo
        forecasts = Forecasts.objects.filter(
            date__gte=start_date
        ).order_by('date')
        
        # Limitamos a un máximo de 30 puntos para mejor visualización
        total_forecasts = forecasts.count()
        if total_forecasts > 30:
            step = total_forecasts // 30
            forecast_ids = forecasts.values_list('id', flat=True)
            sampled_ids = forecast_ids[::step]
            forecasts = Forecasts.objects.filter(id__in=sampled_ids).order_by('date')
        
        context['has_forecasts'] = forecasts.exists()

        if context['has_forecasts']:
            forecasts_list = list(forecasts)

            def _region_temp(f, region_key, period):
                data = getattr(f, region_key)
                return float(data[period]['temp']) if data and data.get(period) and data[period].get('temp') else 0.0

            context['temperature_labels'] = [f.date.strftime('%d/%m') for f in forecasts_list]
            context['max_temperatures_north'] = [_region_temp(f, 'north', 'afternoon') for f in forecasts_list]
            context['min_temperatures_north'] = [_region_temp(f, 'north', 'night') for f in forecasts_list]
            context['max_temperatures_south'] = [_region_temp(f, 'south', 'afternoon') for f in forecasts_list]
            context['min_temperatures_south'] = [_region_temp(f, 'south', 'night') for f in forecasts_list]
            context['max_temperatures_inland'] = [_region_temp(f, 'interior', 'afternoon') for f in forecasts_list]
            context['min_temperatures_inland'] = [_region_temp(f, 'interior', 'night') for f in forecasts_list]

        # Última alerta activa de cada tipo (SOLO UNA)
        now = timezone.now()
        
        # Para cada tipo, obtener solo el más reciente que esté vigente
        # EarlyWarning: usar valid_until para determinar si está activo
        latest_early_warning = EarlyWarning.objects.filter(
            valid_until__gte=now
        ).order_by('-date').first()
        
        # TropicalCyclone: usar valid_until para determinar si está activo
        latest_tropical_cyclone = TropicalCyclone.objects.filter(
            valid_until__gte=now
        ).order_by('-date').first()
        
        # StormWarning: usar valid_until si existe, si no, usar el más reciente
        try:
            latest_storm_warning = StormWarning.objects.filter(
                valid_until__gte=now
            ).order_by('-date').first()
        except FieldError:
            # Si StormWarning no tiene campo valid_until, tomar el más reciente
            latest_storm_warning = StormWarning.objects.order_by('-date').first()
        
        context['latest_alerts'] = {
            'early_warnings': [latest_early_warning] if latest_early_warning else [],
            'tropical_cyclones': [latest_tropical_cyclone] if latest_tropical_cyclone else [],
            'storm_warnings': [latest_storm_warning] if latest_storm_warning else [],
        }

        # Datos exclusivos para superusuarios
        if user.is_superuser:
            context['user_stats'] = {
                'total_users': User.objects.count(),
                'active_today': User.objects.filter(last_login__date=timezone.now().date()).count(),
                'staff_users': User.objects.filter(is_staff=True).count(),
            }

            # Grupos y permisos
            permission_groups = Group.objects.annotate(
                user_count=Count('user')
            ).prefetch_related('permissions').order_by('-user_count')
            paginator_groups = Paginator(permission_groups, 2)
            page_number_groups = self.request.GET.get('page_groups')
            context['permission_groups_page'] = paginator_groups.get_page(page_number_groups)

            # Últimos inicios de sesión
            recent_logins = User.objects.filter(
                last_login__gte=timezone.now() - timezone.timedelta(hours=24)
            ).order_by('-last_login')
            paginator_logins = Paginator(recent_logins, 2)
            page_number_logins = self.request.GET.get('page_logins')
            context['recent_logins_page'] = paginator_logins.get_page(page_number_logins)

            # Sesiones activas
            context['active_sessions'] = Session.objects.filter(
                expire_date__gt=timezone.now()
            ).count()

        return context
class MaintenanceModeToggleView(UserPassesTestMixin, TemplateView):
    template_name = 'pages/dashboard/maintenance_mode/toggle_maintenance.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        config, created = SiteConfiguration.objects.get_or_create()
        context['config'] = config
        context['title'] = 'Modo de Mantenimiento'
        context['parent'] = ''
        context['segment'] = 'maintenance'
        return context

    def post(self, request, *args, **kwargs):
        config, created = SiteConfiguration.objects.get_or_create()
        if config:
            # Actualizar el estado del modo de mantenimiento
            maintenance_mode = 'maintenance_mode' in request.POST
            config.maintenance_mode = maintenance_mode
            config.save()

            # Registrar la acción en los logs
            log_action(
                user=request.user,
                obj=request.user,  # El objeto aquí es el usuario que realiza la acción
                action_flag=6,  # Código para activación/desactivación del mantenimiento
                message=f"El usuario {request.user.username} {'activó' if maintenance_mode else 'desactivó'} el modo de mantenimiento."
            )

            # Mensaje flash para el usuario
            state = "activado" if config.maintenance_mode else "desactivado"
            messages.success(request, f"El modo de mantenimiento ha sido {state}.")
        
        return redirect('toggle_maintenance_mode')

    def test_func(self):
        return self.request.user.is_superuser
