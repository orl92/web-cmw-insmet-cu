import datetime as dt

import pandas as pd
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import Group, User
from django.contrib.sessions.models import Session
from django.core.exceptions import ObjectDoesNotExist
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

        forecats = {
            'ntm': df.values[2][1],
            'nta': df.values[2][2],
            'ntn': df.values[2][3],
            'nwm': df.values[2][4],
            'nwa': df.values[2][5],
            'nwn': df.values[2][6],
            'nwddm': df.values[2][7],
            'nwdda': df.values[2][8],
            'nwddn': df.values[2][9],
            'nwdfm': df.values[2][10],
            'nwdfa': df.values[2][11],
            'nwdfn': df.values[2][12],
            'nsm': df.values[2][13],
            'nsa': df.values[2][14],
            'nsn': df.values[2][15],
            'itm': df.values[3][1],
            'ita': df.values[3][2],
            'itn': df.values[3][3],
            'iwm': df.values[3][4],
            'iwa': df.values[3][5],
            'iwn': df.values[3][6],
            'iwddm': df.values[3][7],
            'iwdda': df.values[3][8],
            'iwddn': df.values[3][9],
            'iwdfm': df.values[3][10],
            'iwdfa': df.values[3][11],
            'iwdfn': df.values[3][12],
            'stm': df.values[4][1],
            'sta': df.values[4][2],
            'stn': df.values[4][3],
            'swm': df.values[4][4],
            'swa': df.values[4][5],
            'swn': df.values[4][6],
            'swddm': df.values[4][7],
            'swdda': df.values[4][8],
            'swddn': df.values[4][9],
            'swdfm': df.values[4][10],
            'swdfa': df.values[4][11],
            'swdfn': df.values[4][12],
            'ssm': df.values[4][13],
            'ssa': df.values[4][14],
            'ssn': df.values[4][15],
            'day1_min_temp': df.values[8][2],
            'day1_max_temp': df.values[8][3],
            'day1_weather': df.values[8][4],
            'day2_min_temp': df.values[9][2],
            'day2_max_temp': df.values[9][3],
            'day2_weather': df.values[9][4],
            'day3_min_temp': df.values[10][2],
            'day3_max_temp': df.values[10][3],
            'day3_weather': df.values[10][4],
            'day4_min_temp': df.values[11][2],
            'day4_max_temp': df.values[11][3],
            'day4_weather': df.values[11][4],
            'day5_min_temp': df.values[12][2],
            'day5_max_temp': df.values[12][3],
            'day5_weather': df.values[12][4],
            'lp': df.values[14][1],
            'nlp': df.values[14][2],
            'nlpd': df.values[14][3].strftime("%Y-%m-%d"),
            'sunrise': df.values[15][1].strftime("%H:%M"),
            'sunset': (dt.datetime.combine(dt.date(1, 1, 1), df.values[16][1]) + dt.timedelta(hours=12)).strftime("%H:%M"),
            'uv_index': df.values[17][1],
        }

        return JsonResponse(forecats)


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
            context['latest_forecast'] = Forecasts.objects.latest('date')
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
            
            context['temperature_labels'] = [f.date.strftime('%d/%m') for f in forecasts_list]
            context['max_temperatures_north'] = [float(f.nta) for f in forecasts_list]
            context['min_temperatures_north'] = [float(f.ntn) for f in forecasts_list]
            context['max_temperatures_south'] = [float(f.sta) for f in forecasts_list]
            context['min_temperatures_south'] = [float(f.stn) for f in forecasts_list]
            context['max_temperatures_inland'] = [float(f.ita) for f in forecasts_list]
            context['min_temperatures_inland'] = [float(f.itn) for f in forecasts_list]

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
            previous_state = config.maintenance_mode
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
