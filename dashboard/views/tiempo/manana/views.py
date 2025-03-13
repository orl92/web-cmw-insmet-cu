from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin,
                                        UserPassesTestMixin)
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from dashboard.forms.tiempo.manana.forms import WeatherTomorrowForm
from dashboard.models import WeatherTomorrow

from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from common.utils import log_action

# Create your views here. 

class WeatherTomorrowListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    template_name = 'pages/dashboard/tiempo/manana/listado_tiempo_m.html'
    model = WeatherTomorrow
    permission_required = 'dashboard.view_weather_tomorrow'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Listado del Tiempo para Mañana'
        context['parent'] = 'tiempo'
        context['segment'] = 'tiempo_m'
        context['btn'] = 'Añadir Tiempo Mañana'
        context['url_create'] = reverse_lazy('crear_tiempo_m')
        context['url_list'] = reverse_lazy('listado_tiempo_m')
        context['objects'] = WeatherTomorrow.objects.all()
        return context 

class WeatherTomorrowCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = WeatherTomorrow
    form_class = WeatherTomorrowForm
    template_name = 'pages/dashboard/tiempo/manana/crear_tiempo_m.html'
    permission_required = 'dashboard.add_weather_tomorrow'
    success_url = reverse_lazy('listado_tiempo_m')
    url_redirect = success_url

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.date = timezone.now() + timedelta(days=1)
        instance.save()
        response = super().form_valid(form)
        
        # Registro de acción
        log_action(
            user=self.request.user,
            obj=self.object,
            action_flag=ADDITION,
            message=f"Se creó un nuevo pronóstico del tiempo para mañana: {self.object.date}."
        )
        
        messages.success(self.request, 'El pronóstico del tiempo para mañana ha sido creado con éxito.', extra_tags='success')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Añadir Tiempo para Mañana'
        context['parent'] = 'tiempo'
        context['segment'] = 'tiempo_m'
        context['url_list'] = reverse_lazy('listado_tiempo_m')
        return context

class WeatherTomorrowUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin, UpdateView):
    model = WeatherTomorrow
    form_class = WeatherTomorrowForm
    template_name = 'pages/dashboard/tiempo/manana/actualizar_tiempo_m.html'
    permission_required = 'dashboard.change_weather_tomorrow'
    success_url = reverse_lazy('listado_tiempo_m')
    url_redirect = success_url

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(WeatherTomorrow, uuid=uuid)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.date = timezone.now() + timedelta(days=1)
        instance.save()
        response = super().form_valid(form)
        
        # Registro de acción
        log_action(
            user=self.request.user,
            obj=self.object,
            action_flag=CHANGE,
            message=f"Se actualizó el pronóstico del tiempo para mañana: {self.object.date}."
        )
        
        messages.success(self.request, 'El pronóstico del tiempo para mañana ha sido actualizado con éxito.', extra_tags='success')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Actualizar Tiempo para Mañana'
        context['parent'] = 'tiempo'
        context['segment'] = 'tiempo_m'
        context['url_list'] = reverse_lazy('listado_tiempo_m')
        return context

    def test_func(self):
        return self.request.user.is_superuser or self.get_object().user == self.request.user

class WeatherTomorrowDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = WeatherTomorrow
    template_name = 'pages/dashboard/tiempo/manana/eliminar_tiempo_m.html'
    permission_required = 'dashboard.delete_weather_tomorrow'
    success_url = reverse_lazy('listado_tiempo_m')
    url_redirect = success_url
    
    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(WeatherTomorrow, uuid=uuid)

    def post(self, request, *args, **kwargs):
        weather_tomorrow = self.get_object()
        
        # Registro de acción antes de eliminar
        log_action(
            user=self.request.user,
            obj=weather_tomorrow,
            action_flag=DELETION,
            message=f"Se eliminó el pronóstico del tiempo para mañana: {weather_tomorrow.date}."
        )
        
        try:
            weather_tomorrow.delete()
            messages.success(request, 'El tiempo para mañana ha sido eliminado con éxito.', extra_tags='danger')
        except Exception as e:
            messages.error(request, str(e))
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Eliminar Tiempo para Mañana'
        context['parent'] = 'tiempo'
        context['segment'] = 'tiempo_m'
        context['url_list'] = reverse_lazy('listado_tiempo_m')
        return context
