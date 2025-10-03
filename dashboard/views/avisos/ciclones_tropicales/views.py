from datetime import datetime
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib import messages
from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin,
                                        UserPassesTestMixin)
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import *

from core import settings
from dashboard.data.mail_send_warning import mail_send_warning
from dashboard.forms.avisos.ciclones_tropicales.forms import \
    TropicalCycloneForm
from dashboard.models import TropicalCyclone

from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from common.utils import log_action

import os
import base64
from django.conf import settings
from django.http import HttpResponse
from django.template.loader import get_template
from io import BytesIO
from xhtml2pdf import pisa

# Create your views here. 

class TropicalCycloneListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    template_name = 'pages/dashboard/avisos/ciclones_tropicales/avisos_ciclones_tropicales.html'
    model = TropicalCyclone
    permission_required = 'dashboard.view_tropical_cyclone'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Ciclones Tropicales'
        context['parent'] = 'avisos'
        context['segment'] = 'cyclone'
        context['btn'] = ('Añadir Aviso Ciclón Tropical')
        context['url_create'] = reverse_lazy('crear_aviso_ciclon_tropical')
        context['url_list'] = reverse_lazy('ciclones_tropicales')
        context['objects'] = TropicalCyclone.objects.all()
        return context

class TropicalCycloneCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = TropicalCyclone
    form_class = TropicalCycloneForm
    template_name = 'pages/dashboard/avisos/ciclones_tropicales/crear_aviso_ciclon_tropical.html'
    permission_required = 'dashboard.add_tropical_cyclone'
    success_url = reverse_lazy('ciclones_tropicales')
    url_redirect = success_url

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Registro de acción
        log_action(
            user=self.request.user,
            obj=self.object,
            action_flag=ADDITION,
            message=f"Se creó un nuevo aviso de ciclón tropical para el: {self.object.date.strftime('%d-%m-%Y')}."
        )
        
        messages.success(self.request, 'El aviso de ciclón tropical ha sido creado con éxito.', extra_tags='success')

        subject = f'Aviso de Ciclon Tropical: {self.object.date}'
        mail_send_warning(self.request, self.object, subject)
        
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Añadir Aviso Ciclón Tropical'
        context['parent'] = 'avisos'
        context['segment'] = 'cyclone'
        context['url_list'] = reverse_lazy('ciclones_tropicales')
        return context

class TropicalCycloneUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin, UpdateView):
    model = TropicalCyclone
    form_class = TropicalCycloneForm
    template_name = 'pages/dashboard/avisos/ciclones_tropicales/actualizar_aviso_ciclon_tropical.html'
    permission_required = 'dashboard.change_tropical_cyclone'
    success_url = reverse_lazy('ciclones_tropicales')
    url_redirect = success_url

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(TropicalCyclone, uuid=uuid)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        # Almacenar los valores originales del objeto antes de cualquier actualización
        original_object = self.get_object(queryset=None)
        relevant_fields = ['summary', 'file', 'valid_until']
        
        # Detectar si hay cambios en los campos relevantes
        has_changes = any(
            form.cleaned_data[field] != getattr(original_object, field)
            for field in relevant_fields
        )

        response = super().form_valid(form)  # Guarda los cambios del formulario

        # Registro de acción
        log_action(
            user=self.request.user,
            obj=self.object,
            action_flag=CHANGE,
            message=f"Se actualizó el aviso de ciclón tropical del: {self.object.date.strftime('%d-%m-%Y')}."
        )

        # Enviar correo solo si hay cambios
        if has_changes:
            subject = f'Aviso de Ciclon Tropical Actualizado: {self.object.date}'
            mail_send_warning(self.request, self.object, subject)

        # Mensaje de éxito en la actualización del aviso
        messages.success(self.request, 'El aviso de ciclón tropical ha sido actualizado con éxito.', extra_tags='success')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Actualizar Aviso Ciclón Tropical'
        context['parent'] = 'avisos'
        context['segment'] = 'cyclone'
        context['url_list'] = reverse_lazy('ciclones_tropicales')
        return context

    def test_func(self):
        return self.request.user.is_superuser or self.get_object().user == self.request.user

class TropicalCycloneDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = TropicalCyclone
    template_name = 'pages/dashboard/avisos/ciclones_tropicales/eliminar_aviso_ciclon_tropical.html'
    permission_required = 'dashboard.delete_tropical_cyclone'
    success_url = reverse_lazy('ciclones_tropicales')
    url_redirect = success_url

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(TropicalCyclone, uuid=uuid)

    def post(self, request, *args, **kwargs):
        tropical_cyclone = self.get_object()

        # Registro de acción antes de eliminar
        log_action(
            user=self.request.user,
            obj=tropical_cyclone,
            action_flag=DELETION,
            message=f"Se eliminó el aviso de ciclón tropical del: {tropical_cyclone.date.strftime('%d-%m-%Y')}."
        )

        try:
            tropical_cyclone.delete()
            messages.success(request, 'El aviso de ciclón tropical ha sido eliminada con éxito.', extra_tags='danger')
        except Exception as e:
            messages.error(request, str(e))
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Eliminar Aviso Ciclón Tropical'
        context['parent'] = 'avisos'
        context['segment'] = 'cyclone'
        context['url_list'] = reverse_lazy('ciclones_tropicales')
        return context

class TropicalCycloneDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = TropicalCyclone
    template_name = 'pages/dashboard/avisos/ciclones_tropicales/detalle_aviso_ciclon_tropical.html'
    permission_required = 'dashboard.view_tropical_cyclone'
    context_object_name = 'cyclone'  # Nombre del objeto en el contexto

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(TropicalCyclone, uuid=uuid)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Detalle del Aviso de Ciclón Tropical'
        context['parent'] = 'avisos'
        context['segment'] = 'cyclone'
        context['url_list'] = reverse_lazy('ciclones_tropicales')
        return context
    
class TropicalCyclonePDFView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = TropicalCyclone
    permission_required = 'dashboard.view_tropical_cyclone'

    def get(self, request, *args, **kwargs):
        tropical_cyclone = self.get_object()

        # Obtener imagen del logo en formato Base64
        logo_path = os.path.join(settings.BASE_DIR, "static/dist/img/logo.png")
        logo_base64 = self.get_image_base64(logo_path)
        
        # Obtener imagen del tropical_cyclone en Base64 si existe
        image_base64 = None
        if tropical_cyclone.image:  # Asegúrate de que 'image' es el campo de la imagen en tu modelo
            try:
                # Obtener la ruta completa de la imagen
                image_path = tropical_cyclone.image.path
                image_base64 = self.get_image_base64(image_path)
            except Exception as e:
                # Manejar excepción (puedes loguear el error)
                print(f"Error al cargar imagen: {e}")

        # Renderizar template HTML
        template = get_template('pages/dashboard/avisos/ciclones_tropicales/pdf_template.html')
        context = {
            'tropical_cyclone': tropical_cyclone,
            'logo_base64': logo_base64,
            'image_base64': image_base64,  # Pasamos la imagen en base64 al contexto
        }
        html = template.render(context)

        # Crear PDF
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)

        if not pdf.err:
            response = HttpResponse(result.getvalue(), content_type='application/pdf')
            filename = f"ciclon_tropical_{tropical_cyclone.date.strftime('%Y-%m-%d')}.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        return HttpResponse("Error al generar el PDF", status=400)

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(TropicalCyclone, uuid=uuid)

    @staticmethod
    def get_image_base64(image_path):
        """Convierte la imagen en Base64 y detecta su tipo MIME."""
        try:
            # Determinar el tipo de imagen por extensión
            ext = os.path.splitext(image_path)[1].lower()
            if ext in ['.jpg', '.jpeg']:
                mime_type = 'image/jpeg'
            elif ext == '.png':
                mime_type = 'image/png'
            elif ext == '.gif':
                mime_type = 'image/gif'
            else:
                # Tipo por defecto si no se reconoce
                mime_type = 'image/jpeg'
            
            with open(image_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
                # Formato: data:<mime_type>;base64,<encoded_string>
                return f"data:{mime_type};base64,{encoded_string}"
        except Exception as e:
            print(f"Error al convertir imagen a base64: {e}")
            return None