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
from dashboard.forms.tiempo.manana.forms import WeatherTomorrowForm
from dashboard.models import WeatherTomorrow

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
        context['is_staff'] = self.request.user.is_staff or self.request.user.is_superuser
        context['is_superuser'] = self.request.user.is_superuser
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
        instance.date = timezone.now()# + timedelta(days=1)
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

        subject = 'El Tiempo para Mañana'
        mail_send(self.request, self.object, subject, 'tiempo_m')

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
            subject = 'El Tiempo para mañana Actualiozado'
            mail_send(self.request, self.object, subject, 'tiempo_m')

        # Mensaje de éxito tras la actualización
        messages.success(self.request, 'El pronóstico del tiempo para mañana ha sido actualizado con éxito.',
                         extra_tags='success')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Actualizar Tiempo para mañana'
        context['parent'] = 'tiempo'
        context['segment'] = 'tiempo_m'
        context['url_list'] = reverse_lazy('listado_tiempo_m')
        return context

    def test_func(self):
        return self.request.user.is_superuser or self.get_object().user == self.request.user

class WeatherTomorrowDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'dashboard.delete_weather_tomorrow'

    def post(self, request, uuid):
        weather_tomorrow = get_object_or_404(WeatherTomorrow, uuid=uuid)
        log_action(
            user=self.request.user,
            obj=weather_tomorrow,
            action_flag=DELETION,
            message=f"Se eliminó el tiempo de mañana del: {weather_tomorrow.date.strftime('%d-%m-%Y')}."
        )
        try:
            weather_tomorrow.delete()
            messages.success(request, 'El tiempo de mañana ha sido eliminado con éxito.')
        except Exception as e:
            messages.error(request, str(e))
        return redirect('listado_tiempo_m')

class WeatherTomorrowDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = WeatherTomorrow
    template_name = 'pages/dashboard/tiempo/manana/detalle_tiempo_m.html'
    permission_required = 'dashboard.view_weather_tomorrow'
    context_object_name = 'weather_tomorrow'  # Nombre del objeto en el contexto

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(WeatherTomorrow, uuid=uuid)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Detalle Tiempo para Mañana'
        context['parent'] = 'tiempo'
        context['segment'] = 'tiempo_m'
        context['url_list'] = reverse_lazy('listado_tiempo_m')
        return context

class WeatherTomorrowPDFView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = WeatherTomorrow
    permission_required = 'dashboard.view_weather_tomorrow'

    def get(self, request, *args, **kwargs):
        weather_tomorrow = self.get_object()

        # Obtener imagen en formato Base64
        logo_path = os.path.join(settings.BASE_DIR, "static/dist/img/logo.png")
        logo_base64 = self.get_image_base64(logo_path)
        
        # Renderizar template HTML
        template = get_template('pages/dashboard/tiempo/manana/pdf_template.html')
        context = {'weather_tomorrow': weather_tomorrow, 'logo_base64': logo_base64}
        html = template.render(context)

        # Crear PDF
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)

        if not pdf.err:
            response = HttpResponse(result.getvalue(), content_type='application/pdf')
            filename = f"tiempo_mañana_{weather_tomorrow.date.strftime('%Y-%m-%d')}.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        return HttpResponse("Error al generar el PDF", status=400)

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(WeatherTomorrow, uuid=uuid)

    @staticmethod
    def get_image_base64(image_path):
        """Convierte la imagen en Base64."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
