from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UserPassesTestMixin,
)
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, ListView, UpdateView, View

from apps.core.utils import log_action
from apps.meteo.forms.forecast import (
    ForecastExtendedDayFormSet,
    ForecastRegionsFormSet,
    ForecastsForm,
)
from apps.meteo.models import REGION_HAS_SEA, Forecasts
from apps.meteo.utils.excel_forecast import build_template, parse_excel

APPLICATION_SPREADSHEET = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

REGION_MAP = {'north': 'n', 'interior': 'i', 'south': 's'}
PERIOD_MAP = {'morning': 'm', 'afternoon': 'a', 'night': 'n'}


def _build_region_initial():
    initial = []
    for region in REGION_MAP:
        for period in PERIOD_MAP:
            initial.append(
                {
                    'region': region,
                    'period': period,
                    'temp': '',
                    'weather': '',
                    'wind_dir': '',
                    'wind_speed': '',
                    'sea_note': '' if REGION_HAS_SEA[region] else None,
                }
            )
    return initial


def _formset_errors(*formsets):
    """Recolecta los errores de campo y no-de-campo de uno o más formsets."""
    errors = []
    for formset in formsets:
        errors.extend(formset.non_form_errors())
        for each_form in formset.forms:
            errors.extend(each_form.errors.values())
    return errors


def _build_extended_initial(date_value):
    initial = []
    for day_num in range(1, 6):
        initial.append(
            {
                'day_number': day_num,
                'date': (date_value + timedelta(days=day_num)).strftime('%Y-%m-%d')
                if date_value
                else '',
                'min_temp': '',
                'max_temp': '',
                'weather': '',
            }
        )
    return initial


class ForecastsListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Forecasts
    template_name = 'pages/meteo/forecast/list.html'
    permission_required = 'meteo.view_forecast'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Listado de Pronósticos'
        context['parent'] = ''
        context['segment'] = 'pronostico'
        context['btn'] = 'Añadir Pronóstico'
        context['url_create'] = reverse_lazy('meteo:pronostico_create')
        context['url_list'] = reverse_lazy('meteo:pronostico_list')
        context['is_superuser'] = self.request.user.is_superuser

        date = self._parse_date_filter(self.request.GET.get('date'))

        context['date'] = date.strftime('%d/%m/%Y')
        context['date_iso'] = date.strftime('%Y-%m-%d')
        forecasts = Forecasts.objects.filter(date=date).prefetch_related('regions', 'extended_days')
        context['forecasts'] = forecasts
        context['has_data'] = forecasts.exists()
        return context

    @staticmethod
    def _parse_date_filter(date_string):
        if not date_string:
            return timezone.localdate()
        for fmt in ('%d/%m/%Y', '%Y-%m-%d'):
            try:
                return datetime.strptime(date_string, fmt).date()
            except ValueError:
                continue
        return timezone.localdate()


class AllForecastCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Forecasts
    form_class = ForecastsForm
    template_name = 'pages/meteo/forecast/form.html'
    permission_required = 'meteo.add_forecast'
    success_url = reverse_lazy('meteo:pronostico_list')

    def get_date_value(self):
        date_string = self.request.POST.get('date') or self.request.GET.get('date')
        if not date_string:
            return timezone.localdate()
        for fmt in ('%d/%m/%Y', '%Y-%m-%d'):
            try:
                return datetime.strptime(date_string, fmt).date()
            except ValueError:
                continue
        return timezone.localdate()

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
            context['region_formset'] = ForecastRegionsFormSet(
                self.request.POST, instance=Forecasts()
            )
            context['extended_formset'] = ForecastExtendedDayFormSet(
                self.request.POST, instance=Forecasts()
            )
        else:
            context['region_formset'] = ForecastRegionsFormSet(
                instance=Forecasts(), initial=_build_region_initial()
            )
            context['extended_formset'] = ForecastExtendedDayFormSet(
                instance=Forecasts(), initial=_build_extended_initial(date_val)
            )
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        region_formset = ForecastRegionsFormSet(self.request.POST, instance=self.object)
        extended_formset = ForecastExtendedDayFormSet(self.request.POST, instance=self.object)
        errors = _formset_errors(region_formset, extended_formset)
        if errors:
            messages.error(self.request, 'Corrija los errores del formulario.')
            context = self.get_context_data(form=form)
            context['region_formset'] = region_formset
            context['extended_formset'] = extended_formset
            return self.render_to_response(context)

        self.object.save()
        region_formset.save()
        extended_formset.save()

        log_action(
            user=self.request.user,
            obj=self.object,
            action_flag=ADDITION,
            message=(
                f'Se creó un nuevo pronóstico para el: {self.object.date.strftime("%d-%m-%Y")}.'
            ),
        )
        messages.success(
            self.request, 'El pronóstico ha sido creado con éxito.', extra_tags='success'
        )
        return redirect(self.success_url)


class ForecastUpdateView(
    LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin, UpdateView
):
    model = Forecasts
    form_class = ForecastsForm
    template_name = 'pages/meteo/forecast/form.html'
    permission_required = 'meteo.change_forecast'
    success_url = reverse_lazy('meteo:pronostico_list')

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(Forecasts, uuid=uuid)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Actualizar Pronóstico'
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
            context['region_formset'] = ForecastRegionsFormSet(
                self.request.POST, instance=self.object
            )
            context['extended_formset'] = ForecastExtendedDayFormSet(
                self.request.POST, instance=self.object
            )
        else:
            context['region_formset'] = ForecastRegionsFormSet(instance=self.object)
            context['extended_formset'] = ForecastExtendedDayFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        region_formset = ForecastRegionsFormSet(self.request.POST, instance=self.object)
        extended_formset = ForecastExtendedDayFormSet(self.request.POST, instance=self.object)
        errors = _formset_errors(region_formset, extended_formset)
        if errors:
            messages.error(self.request, 'Corrija los errores del formulario.')
            context = self.get_context_data(form=form)
            context['region_formset'] = region_formset
            context['extended_formset'] = extended_formset
            return self.render_to_response(context)

        self.object.save()
        region_formset.save()
        extended_formset.save()

        log_action(
            user=self.request.user,
            obj=self.object,
            action_flag=CHANGE,
            message=f'Se actualizó el pronóstico del: {self.object.date.strftime("%d-%m-%Y")}.',
        )
        messages.success(
            self.request, 'El pronóstico ha sido actualizado con éxito.', extra_tags='warning'
        )
        return redirect(self.success_url)

    def test_func(self):
        return self.request.user.is_superuser


class ForecastDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'meteo.delete_forecast'

    def post(self, request, uuid):
        forecast = get_object_or_404(Forecasts, uuid=uuid)
        log_action(
            user=self.request.user,
            obj=forecast,
            action_flag=DELETION,
            message=f'Se eliminó el pronóstico del: {forecast.date.strftime("%d-%m-%Y")}.',
        )
        try:
            forecast.delete()
            messages.success(request, 'El pronóstico ha sido eliminado con éxito.')
        except Exception as e:
            messages.error(request, str(e))
        return redirect('meteo:pronostico_list')


class ExcelJSONView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'meteo.change_forecast'

    def post(self, request):
        excel = request.FILES.get('excelFile')
        if not excel:
            return JsonResponse({'error': 'No se envió el archivo'}, status=400)

        data = parse_excel(excel)
        if 'error' in data:
            return JsonResponse({'error': data['error']}, status=400)
        return JsonResponse(data)


class ForecastExcelTemplateView(LoginRequiredMixin, View):
    def get(self, request):
        content = build_template()
        response = HttpResponse(content, content_type=APPLICATION_SPREADSHEET)
        response['Content-Disposition'] = 'attachment; filename="plantilla_pronostico.xlsx"'
        return response
