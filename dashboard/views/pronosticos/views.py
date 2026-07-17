from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UserPassesTestMixin)
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, ListView, UpdateView, View

from common.utils import log_action
from dashboard.forms.pronosticos.forms import (
    ForecastExtendedDayFormSet,
    ForecastRegionsFormSet,
    ForecastsForm,
)
from dashboard.models import Forecasts

REGION_MAP = {'north': 'n', 'interior': 'i', 'south': 's'}
PERIOD_MAP = {'morning': 'm', 'afternoon': 'a', 'night': 'n'}
REGION_HAS_SEA = {'north': True, 'interior': False, 'south': True}


def _build_region_initial():
    initial = []
    for region in REGION_MAP:
        for period in PERIOD_MAP:
            initial.append({
                'region': region,
                'period': period,
                'temp': '',
                'weather': '',
                'wind_dir': '',
                'wind_speed': '',
                'sea_note': '' if REGION_HAS_SEA[region] else None,
            })
    return initial


def _build_extended_initial(date_value):
    initial = []
    for day_num in range(1, 6):
        initial.append({
            'day_number': day_num,
            'date': (date_value + timedelta(days=day_num)).strftime('%Y-%m-%d') if date_value else '',
            'min_temp': '',
            'max_temp': '',
            'weather': '',
        })
    return initial


class ForecastsListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Forecasts
    template_name = 'pages/dashboard/pronosticos/pronosticos.html'
    permission_required = 'dashboard.view_forecast'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Listado de Pronósticos'
        context['parent'] = ''
        context['segment'] = 'pronostico'
        context['btn'] = 'Añadir Pronóstico'
        context['url_create'] = reverse_lazy('crear_pronostico')
        context['url_list'] = reverse_lazy('pronosticos')
        context['is_staff'] = self.request.user.is_staff or self.request.user.is_superuser
        context['is_superuser'] = self.request.user.is_superuser

        date_string = self.request.GET.get('date')
        if date_string:
            date = datetime.strptime(date_string, '%Y-%m-%d').date()
        else:
            date = timezone.now().date()

        context['date'] = date.strftime('%Y-%m-%d')
        forecasts = Forecasts.objects.filter(date=date).prefetch_related('regions', 'extended_days')
        context['forecasts'] = forecasts
        context['has_data'] = forecasts.exists()
        return context


class AllForecastCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Forecasts
    form_class = ForecastsForm
    template_name = 'pages/dashboard/pronosticos/crear_pronostico.html'
    permission_required = 'dashboard.add_forecast'
    success_url = reverse_lazy('pronosticos')

    def get_date_value(self):
        date_string = self.request.GET.get('date')
        if date_string:
            return datetime.strptime(date_string, '%Y-%m-%d').date()
        return timezone.now().date()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        date_val = self.get_date_value()
        context['title'] = 'Añadir Pronostico'
        context['parent'] = ''
        context['segment'] = 'pronostico'
        context['url_list'] = self.success_url
        context['date'] = date_val.strftime('%Y-%m-%d')
        context['region_config'] = [
            ('Costa Norte', 'north', True),
            ('Interior', 'interior', False),
            ('Costa Sur', 'south', True),
        ]

        if self.request.POST:
            context['region_formset'] = ForecastRegionsFormSet(self.request.POST, instance=Forecasts())
            context['extended_formset'] = ForecastExtendedDayFormSet(self.request.POST, instance=Forecasts())
        else:
            context['region_formset'] = ForecastRegionsFormSet(
                instance=Forecasts(), initial=_build_region_initial()
            )
            context['extended_formset'] = ForecastExtendedDayFormSet(
                instance=Forecasts(), initial=_build_extended_initial(date_val)
            )
        return context

    def form_valid(self, form):
        self.object = form.save()
        region_formset = ForecastRegionsFormSet(self.request.POST, instance=self.object)
        extended_formset = ForecastExtendedDayFormSet(self.request.POST, instance=self.object)
        if region_formset.is_valid():
            region_formset.save()
        if extended_formset.is_valid():
            extended_formset.save()

        log_action(
            user=self.request.user,
            obj=self.object,
            action_flag=ADDITION,
            message=f"Se cre\u00f3 un nuevo pron\u00f3stico para el: {self.object.date.strftime('%d-%m-%Y')}."
        )
        messages.success(self.request, 'El pron\u00f3stico ha sido creado con \u00e9xito.', extra_tags='success')
        return redirect(self.success_url)


class ForecastUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Forecasts
    form_class = ForecastsForm
    template_name = 'pages/dashboard/pronosticos/actualizar_pronostico.html'
    permission_required = 'dashboard.change_forecast'
    success_url = reverse_lazy('pronosticos')

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(Forecasts, uuid=uuid)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Actualizar Pron\u00f3stico'
        context['parent'] = ''
        context['segment'] = 'pronostico'
        context['url_list'] = self.success_url
        context['region_config'] = [
            ('Costa Norte', 'north', True),
            ('Interior', 'interior', False),
            ('Costa Sur', 'south', True),
        ]
        context['date'] = self.object.date.strftime('%Y-%m-%d')

        if self.request.POST:
            context['region_formset'] = ForecastRegionsFormSet(self.request.POST, instance=self.object)
            context['extended_formset'] = ForecastExtendedDayFormSet(self.request.POST, instance=self.object)
        else:
            context['region_formset'] = ForecastRegionsFormSet(instance=self.object)
            context['extended_formset'] = ForecastExtendedDayFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        self.object = form.save()
        region_formset = ForecastRegionsFormSet(self.request.POST, instance=self.object)
        extended_formset = ForecastExtendedDayFormSet(self.request.POST, instance=self.object)
        if region_formset.is_valid():
            region_formset.save()
        if extended_formset.is_valid():
            extended_formset.save()

        log_action(
            user=self.request.user,
            obj=self.object,
            action_flag=CHANGE,
            message=f"Se actualiz\u00f3 el pron\u00f3stico del: {self.object.date.strftime('%d-%m-%Y')}."
        )
        messages.success(self.request, 'El pron\u00f3stico ha sido actualizado con \u00e9xito.', extra_tags='warning')
        return redirect(self.success_url)

    def test_func(self):
        return self.request.user.is_superuser or self.get_object().user == self.request.user


class ForecastDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'dashboard.delete_forecasts'

    def post(self, request, uuid):
        forecast = get_object_or_404(Forecasts, uuid=uuid)
        log_action(
            user=self.request.user,
            obj=forecast,
            action_flag=DELETION,
            message=f"Se elimin\u00f3 el pron\u00f3stico del: {forecast.date.strftime('%d-%m-%Y')}."
        )
        try:
            forecast.delete()
            messages.success(request, 'El pron\u00f3stico ha sido eliminado con \u00e9xito.')
        except Exception as e:
            messages.error(request, str(e))
        return redirect('pronosticos')
