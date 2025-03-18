import datetime as dt
import pandas as pd
from django.contrib import messages
from django.http import JsonResponse
from django.views import View
from django.shortcuts import redirect, render
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView
from django.contrib.auth.models import User, Group
from django.contrib.sessions.models import Session
from django.utils import timezone
from django.db.models import Count
from django.core.paginator import Paginator
from django.core.exceptions import ObjectDoesNotExist

from common.utils import log_action
from dashboard.models import EarlyWarning, Forecasts, RadarWarning, SiteConfiguration, SpecialNotice, TropicalCyclone, WeatherCommentary

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
        # Verifica si el usuario es staff antes de procesar la solicitud
        if not request.user.is_staff:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
    
    def test_func(self):
        # Solo usuarios con is_staff = True pueden acceder
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        # Datos base para todos los usuarios
        context.update({
            'title': 'Dashboard',
            'parent': '',
            'segment': 'dashboard',
            'is_superuser': user.is_superuser,
        })
        # Datos meteorológicos comunes
        try:
            context['latest_forecast'] = Forecasts.objects.latest('date')
        except ObjectDoesNotExist:
            context['latest_forecast'] = None
        # Últimos 7 pronósticos para el gráfico (si existen)
        forecasts = Forecasts.objects.order_by('-date')[:7]
        context['has_forecasts'] = forecasts.exists()
        # Datos para el gráfico de temperaturas
        if context['has_forecasts']:
            context['temperature_labels'] = [f.date.strftime('%d/%m') for f in forecasts]
            context['max_temperatures_north'] = [f.nta for f in forecasts]  # Temperatura tarde (max) costa norte
            context['min_temperatures_north'] = [f.ntn for f in forecasts]  # Temperatura noche (min) costa norte
            context['max_temperatures_south'] = [f.sta for f in forecasts]  # Temperatura tarde (max) costa sur
            context['min_temperatures_south'] = [f.stn for f in forecasts]  # Temperatura noche (min) costa sur
            context['max_temperatures_inland'] = [f.ita for f in forecasts]  # Temperatura tarde (max) interior
            context['min_temperatures_inland'] = [f.itn for f in forecasts]  # Temperatura noche (min) interior
        # Últimas alertas activas (hasta 5)
        context['latest_alerts'] = {
            'early_warnings': EarlyWarning.objects.filter(valid_until__gt=timezone.now()).order_by('-date')[:5],
            'tropical_cyclones': TropicalCyclone.objects.filter(valid_until__gt=timezone.now()).order_by('-date')[:5],
            'special_notices': SpecialNotice.objects.filter(valid_until__gt=timezone.now()).order_by('-date')[:5],
            'radar_warnings': RadarWarning.objects.filter(valid_until__gt=timezone.now()).order_by('-date')[:5],
        }
        # Datos exclusivos para superusuarios
        if user.is_superuser:
            # Estadísticas de usuarios
            context['user_stats'] = {
                'total_users': User.objects.count(),
                'active_today': User.objects.filter(last_login__date=timezone.now().date()).count(),
                'staff_users': User.objects.filter(is_staff=True).count(),
            }
            # Grupos y permisos (con paginación)
            permission_groups = Group.objects.annotate(
                user_count=Count('user')
            ).prefetch_related('permissions').order_by('-user_count')
            paginator = Paginator(permission_groups, 10)  # 10 grupos por página
            page_number = self.request.GET.get('page')
            context['permission_groups_page'] = paginator.get_page(page_number)
            # Últimos inicios de sesión (últimas 24 horas)
            context['recent_logins'] = User.objects.filter(
                last_login__gte=timezone.now() - timezone.timedelta(hours=24)
            ).order_by('-last_login')[:10]
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


