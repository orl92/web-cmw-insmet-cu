import base64
import os
from io import BytesIO

import xhtml2pdf.pisa as pisa
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UserPassesTestMixin)
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import get_template
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DetailView,
    ListView,
    UpdateView,
    View,
)

from common.utils import log_action
from dashboard.data.mail_send import mail_send
from dashboard.forms.tiempo.hoy.forms import WeatherTodayForm
from dashboard.models import WeatherToday

# Create your views here.

class WeatherTodayListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    template_name = 'pages/dashboard/tiempo/hoy/listado_tiempo_h.html'
    model = WeatherToday
    permission_required = 'dashboard.view_weather_today'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Listado del Tiempo para Hoy'
        context['parent'] = 'tiempo'
        context['segment'] = 'tiempo_h'
        context['btn'] = 'Añadir Tiempo para Hoy'
        context['url_create'] = reverse_lazy('crear_tiempo_h')
        context['url_list'] = reverse_lazy('listado_tiempo_h')
        context['is_superuser'] = self.request.user.is_superuser
        context['objects'] = WeatherToday.objects.all()
        return context


class WeatherTodayCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = WeatherToday
    form_class = WeatherTodayForm
    template_name = 'pages/dashboard/tiempo/hoy/crear_tiempo_h.html'
    permission_required = 'dashboard.add_weather_today'
    success_url = reverse_lazy('listado_tiempo_h')
    url_redirect = success_url

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.date = timezone.now()
        instance.save()
        response = super().form_valid(form)

        # Registro de acción
        log_action(
            user=self.request.user,
            obj=self.object,
            action_flag=ADDITION,
            message=f"Se creó un nuevo pronóstico del tiempo para hoy: {self.object.date}."
        )

        messages.success(self.request, 'El pronóstico del tiempo para hoy ha sido creado con éxito.',
                         extra_tags='success')

        subject = 'El Tiempo para Hoy'
        mail_send(self.request, self.object, subject, 'tiempo_h')

        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Añadir Tiempo para Hoy'
        context['parent'] = 'tiempo'
        context['segment'] = 'tiempo_h'
        context['url_list'] = reverse_lazy('listado_tiempo_h')
        return context


class WeatherTodayUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin, UpdateView):
    model = WeatherToday
    form_class = WeatherTodayForm
    template_name = 'pages/dashboard/tiempo/hoy/actualizar_tiempo_h.html'
    permission_required = 'dashboard.change_weather_today'
    success_url = reverse_lazy('listado_tiempo_h')
    url_redirect = success_url

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(WeatherToday, uuid=uuid)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        # Obtener el objeto original antes de los cambios
        original_object = self.get_object(queryset=None)
        relevant_fields = ['summary', 'file', 'email_recipient_list']

        # Detectar cambios en los campos relevantes
        has_changes = any(
            form.cleaned_data[field] != getattr(original_object, field)
            for field in relevant_fields
        )

        # Guardar el formulario actualizado
        instance = form.save(commit=False)
        instance.date = timezone.now()
        instance.save()
        response = super().form_valid(form)

        # Registro de acción
        log_action(
            user=self.request.user,
            obj=self.object,
            action_flag=CHANGE,
            message=f"Se actualizó el pronóstico del tiempo para hoy: {self.object.date}."
        )

        # Enviar correos solo si hay cambios
        if has_changes:
            subject = 'El Tiempo para Hoy Actualiozado'
            mail_send(self.request, self.object, subject, 'tiempo_h')

        # Mensaje de éxito tras la actualización
        messages.success(self.request, 'El pronóstico del tiempo para hoy ha sido actualizado con éxito.',
                         extra_tags='success')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Actualizar Tiempo para Hoy'
        context['parent'] = 'tiempo'
        context['segment'] = 'tiempo_h'
        context['url_list'] = reverse_lazy('listado_tiempo_h')
        return context

    def test_func(self):
        return self.request.user.is_superuser or self.get_object().user == self.request.user


class WeatherTodayDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'dashboard.delete_weather_today'

    def post(self, request, uuid):
        weather_today = get_object_or_404(WeatherToday, uuid=uuid)
        log_action(
            user=self.request.user,
            obj=weather_today,
            action_flag=DELETION,
            message=f"Se eliminó el tiempo de hoy del: {weather_today.date.strftime('%d-%m-%Y')}."
        )
        try:
            weather_today.delete()
            messages.success(request, 'El tiempo de hoy ha sido eliminado con éxito.')
        except Exception as e:
            messages.error(request, str(e))
        return redirect('listado_tiempo_h')

class WeatherTodayDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = WeatherToday
    template_name = 'pages/dashboard/tiempo/hoy/detalle_tiempo_h.html'
    permission_required = 'dashboard.view_weather_today'
    context_object_name = 'weather_today'  # Nombre del objeto en el contexto

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(WeatherToday, uuid=uuid)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Detalle Tiempo para Hoy'
        context['parent'] = 'tiempo'
        context['segment'] = 'tiempo_h'
        context['url_list'] = reverse_lazy('listado_tiempo_h')
        return context


class WeatherTodayPDFView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = WeatherToday
    permission_required = 'dashboard.view_weather_today'

    def get(self, request, *args, **kwargs):
        weather_today = self.get_object()

        # Obtener imagen en formato Base64
        logo_path = os.path.join(settings.BASE_DIR, "static/dist/img/logo.png")
        logo_base64 = self.get_image_base64(logo_path)

        # Renderizar template HTML
        template = get_template('pages/dashboard/tiempo/hoy/pdf_template.html')
        context = {'weather_today': weather_today, 'logo_base64': logo_base64}
        html = template.render(context)

        # Crear PDF
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)

        if not pdf.err:
            response = HttpResponse(result.getvalue(), content_type='application/pdf')
            filename = f"tiempo_hoy_{weather_today.date.strftime('%Y-%m-%d')}.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        return HttpResponse("Error al generar el PDF", status=400)

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(WeatherToday, uuid=uuid)

    @staticmethod
    def get_image_base64(image_path):
        """Convierte la imagen en Base64."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
