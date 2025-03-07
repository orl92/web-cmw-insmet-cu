from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin,
                                        UserPassesTestMixin)
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from dashboard.forms.datos.pronosticos.forms import ForecastsForm
from dashboard.models import Forecasts

from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from common.utils import log_action

# Create your views here.

class ForecastsListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Forecasts
    template_name = 'pages/dashboard/pronosticos/pronosticos.html'
    permission_required = 'dashboard.view_forecast'  # Permiso requerido para ver un pronostico

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Listado de Pronósticos'
        context['parent'] = 'pronosticos'
        context['segment'] = 'pronostico'
        context['btn'] = 'Añadir Pronóstico'
        context['url_create'] = reverse_lazy('crear_pronostico')
        context['url_list'] = reverse_lazy('pronosticos')

        # Obtiene la fecha seleccionada por el usuario desde los parámetros GET de la solicitud
        date_string = self.request.GET.get('date')
        if date_string:
            # Si se proporciona una fecha, la convierte de cadena a objeto de fecha
            date = datetime.strptime(date_string, '%Y-%m-%d').date()
        else:
            # Si no se proporciona una fecha, usa la fecha actual
            date = timezone.now().date()

        # Añade la fecha al contexto, formateada como una cadena para el campo de entrada HTML
        context['date'] = date.strftime('%Y-%m-%d')

        # Filtra los objetos AllForecasts por la fecha seleccionada
        forecasts = Forecasts.objects.filter(date=date)
        context['forecasts'] = forecasts

        # Verifica si hay datos en la tabla
        context['has_data'] = forecasts.exists()

        return context  

class AllForecastCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Forecasts
    form_class = ForecastsForm
    template_name = 'pages/dashboard/pronosticos/crear_pronostico.html'
    permission_required = 'dashboard.add_forecast'  # Permiso requerido para añadir un pronóstico
    success_url = reverse_lazy('pronosticos')
    url_redirect = success_url

    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Registro de acción
        log_action(
            user=self.request.user,
            obj=self.object,
            action_flag=ADDITION,
            message=f"Se creó un nuevo pronóstico para el: {self.object.date.strftime('%d-%m-%Y')}."
        )
        
        messages.success(self.request, 'El pronóstico ha sido creado con éxito.', extra_tags='success')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Añadir Pronostico'
        context['parent'] = 'pronosticos'
        context['segment'] = 'pronostico'
        context['url_list'] = self.success_url

        # Obtiene la fecha seleccionada por el usuario desde los parámetros GET de la solicitud
        date_string = self.request.GET.get('date')
        if date_string:
            date = datetime.strptime(date_string, '%Y-%m-%d').date()
            day_date = [date + timedelta(days=i + 1) for i in range(5)]
        else:
            date = timezone.now().date()
            day_date = [date + timedelta(days=i + 1) for i in range(5)]

        context['date'] = date.strftime('%Y-%m-%d')
        for i in range(5):
            context[f'day{i+1}_date'] = day_date[i].strftime('%Y-%m-%d')

        return context

class ForecastUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Forecasts
    form_class = ForecastsForm
    template_name = 'pages/dashboard/pronosticos/actualizar_pronostico.html'
    permission_required = 'dashboard.change_forecast'  # Permiso requerido para actualizar un pronóstico
    success_url = reverse_lazy('pronosticos')

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(Forecasts, uuid=uuid)
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Registro de acción
        log_action(
            user=self.request.user,
            obj=self.object,
            action_flag=CHANGE,
            message=f"Se actualizó el pronóstico del: {self.object.date.strftime('%d-%m-%Y')}."
        )
        
        messages.success(self.request, 'El pronóstico ha sido actualizado con éxito.', extra_tags='warning')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Actualizar Pronóstico'
        context['parent'] = 'datos'
        context['segment'] = 'pronostico'
        context['url_list'] = self.success_url
        return context
    
    def test_func(self):
        return self.request.user.is_superuser or self.get_object().user == self.request.user

class ForecastDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Forecasts
    template_name = 'pages/dashboard/pronosticos/eliminar_pronostico.html'
    permission_required = 'dashboard.delete_forecasts'
    success_url = reverse_lazy('pronosticos')
    url_redirect = success_url

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(Forecasts, uuid=uuid)

    def post(self, request, *args, **kwargs):
        forecast = self.get_object()
        
        # Registro de acción antes de eliminar
        log_action(
            user=self.request.user,
            obj=forecast,
            action_flag=DELETION,
            message=f"Se eliminó el pronóstico del: {forecast.date.strftime('%d-%m-%Y')}."
        )
        
        try:
            forecast.delete()
            messages.success(request, 'El pronóstico ha sido eliminado con éxito.', extra_tags='danger')
        except Exception as e:
            messages.error(request, str(e))
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Eliminar Pronóstico'
        context['parent'] = 'pronosticos'
        context['segment'] = 'pronostico'
        context['url_list'] = self.success_url
        return context
