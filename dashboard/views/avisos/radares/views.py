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
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView

from core import settings
from dashboard.forms.avisos.radares.forms import RadarWarningForm
from dashboard.models import RadarWarning

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

class RadarWarningListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = RadarWarning
    template_name = 'pages/dashboard/avisos/radares/avisos_radares.html'
    permission_required = 'dashboard.view_radar_warning'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Avisos Radares'
        context['parent'] = 'avisos'
        context['segment'] = 'radar'
        context['btn'] = ('Añadir Aviso Radar')
        context['url_create'] = reverse_lazy('crear_aviso_radar')
        context['url_list'] = reverse_lazy('avisos_radares')
        context['objects'] = RadarWarning.objects.all()
        return context

class RadarWarningCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = RadarWarning
    form_class = RadarWarningForm
    template_name = 'pages/dashboard/avisos/radares/crear_aviso_radar.html'
    permission_required = 'dashboard.add_radar_warning'
    success_url = reverse_lazy('avisos_radares')
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
            message=f"Se creó un nuevo aviso de radar para el: {self.object.date.strftime('%d-%m-%Y')}."
        )
        
        messages.success(self.request, 'El aviso de radar ha sido creado con éxito.', extra_tags='success')
        
        # Construir la URL dinámica para "Ver todas las alertas"
        listado_url = self.request.build_absolute_uri(reverse('radar'))
        index_url = self.request.build_absolute_uri(reverse('index'))
        image_url = self.request.build_absolute_uri(self.object.image.url)
        
        # Obtener la lista seleccionada en el formulario
        recipient_list = self.object.email_recipient_list
        if recipient_list:
            recipients = recipient_list.recipients.values_list('email', flat=True)

            if recipients:
                # Enviar correo
                try:
                    subject = f'Aviso de Radar: {self.object.title}'
                    html_message = render_to_string(
                        'pages/dashboard/emails/notification.html',
                        {
                            'alert': self.object,
                            'listado_url': listado_url,
                            'index_url': index_url,     # URL al índice de la página
                            'image_url': image_url,
                            'current_year': datetime.now().year  # Pasa el año actual
                        }
                    )
                    # Limpia las etiquetas HTML de la descripción, si existe
                    plain_message = strip_tags(html_message)

                    email = EmailMessage(
                        subject=subject,
                        body=html_message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=list(recipients),
                    )
                    email.content_subtype = 'html'
                    email.send()

                    # Mostrar mensaje de éxito para el envío del correo
                    messages.success(self.request, 'El correo de notificación ha sido enviado con éxito.', extra_tags='success')
                except Exception as e:
                    # Manejar errores de envío
                    messages.error(self.request, f'Ocurrió un error al enviar el correo: {str(e)}', extra_tags='danger')
            else:
                messages.warning(self.request, 'La lista de correos seleccionada no tiene destinatarios.', extra_tags='warning')
        else:
            messages.warning(self.request, 'No se seleccionó ninguna lista de correos para esta actualización.', extra_tags='warning')
        
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Añadir Aviso Radar'
        context['parent'] = 'avisos'
        context['segment'] = 'radar'
        context['url_list'] = reverse_lazy('avisos_radares')
        return context

class RadarWarningUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin, UpdateView):
    model = RadarWarning
    form_class = RadarWarningForm
    template_name = 'pages/dashboard/avisos/radares/actualizar_aviso_radar.html'
    permission_required = 'dashboard.change_radar_warning'
    success_url = reverse_lazy('avisos_radares')
    url_redirect = success_url

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(RadarWarning, uuid=uuid)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        # Almacenar los valores originales del objeto antes de cualquier actualización
        original_object = self.get_object(queryset=None)
        relevant_fields = ['title', 'description', 'valid_until']
        
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
            message=f"Se actualizó el aviso de radar del: {self.object.date.strftime('%d-%m-%Y')}."
        )
        
        # Enviar correo solo si hay cambios
        if has_changes:
            # Construir la URL dinámica para el listado de alertas
            listado_url = self.request.build_absolute_uri(reverse('radar'))
            index_url = self.request.build_absolute_uri(reverse('index'))
            image_url = self.request.build_absolute_uri(self.object.image.url)
            
            # Obtener la lista de destinatarios seleccionada
            recipient_list = self.object.email_recipient_list

            if recipient_list:
                recipients = recipient_list.recipients.values_list('email', flat=True)

                from django.utils.html import strip_tags

                # Renderizar el correo electrónico
                subject = f'Aviso de Radar Actualizado: {self.object.title}'
                html_message = render_to_string(
                    'pages/dashboard/emails/notification.html',
                    {
                        'alert': self.object, 
                        'listado_url': listado_url,
                        'index_url': index_url,     # URL al índice de la página
                        'image_url': image_url,
                        'current_year': datetime.now().year  # Pasa el año actual
                     }
                )

                # Limpia la descripción de etiquetas HTML
                plain_description = strip_tags(self.object.description)

                plain_message = strip_tags(html_message).replace(self.object.description, plain_description)

                try:
                    email = EmailMessage(
                        subject=subject,
                        body=html_message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=list(recipients),
                    )
                    email.content_subtype = 'html'
                    email.send()

                    # Mensaje de éxito del envío de correos
                    messages.success(self.request, 'El correo de notificación ha sido enviado con éxito.', extra_tags='success')
                except Exception as e:
                    # Manejo de errores en el envío de correos
                    messages.error(self.request, f'Ocurrió un error al enviar el correo: {str(e)}', extra_tags='danger')
            else:
                # Notificación si no hay destinatarios seleccionados
                messages.warning(self.request, 'No se seleccionó ninguna lista de correos para esta alerta.', extra_tags='warning')
        
        # Mensaje de éxito en la actualización del aviso
        messages.success(self.request, 'El aviso de radar ha sido actualizado con éxito.', extra_tags='success')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Actualizar Aviso Radar'
        context['parent'] = 'avisos'
        context['segment'] = 'radar'
        context['url_list'] = reverse_lazy('avisos_radares')
        return context
    
    def test_func(self):
        return self.request.user.is_superuser or self.get_object().user == self.request.user

class RadarWarningDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = RadarWarning
    template_name = 'pages/dashboard/avisos/radares/eliminar_aviso_radar.html'
    permission_required = 'dashboard.delete_radar_warning'
    success_url = reverse_lazy('avisos_radares')
    url_redirect = success_url

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(RadarWarning, uuid=uuid)

    def post(self, request, *args, **kwargs):
        radar_warning = self.get_object()
        
        # Registro de acción antes de eliminar
        log_action(
            user=self.request.user,
            obj=radar_warning,
            action_flag=DELETION,
            message=f"Se eliminó el aviso de radar del: {radar_warning.date.strftime('%d-%m-%Y')}."
        )
        
        try:
            radar_warning.delete()
            messages.success(request, 'El aviso de radar ha sido eliminada con éxito.', extra_tags='danger')
        except Exception as e:
            messages.error(request, str(e))
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Eliminar Aviso Radar'
        context['parent'] = 'avisos'
        context['segment'] = 'radar'
        context['url_list'] = reverse_lazy('avisos_radares')
        return context

class RadarWarningDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = RadarWarning
    template_name = 'pages/dashboard/avisos/radares/detalle_aviso_radar.html'
    permission_required = 'dashboard.view_radar_warning'
    context_object_name = 'radar'  # Nombre del objeto en el contexto

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(RadarWarning, uuid=uuid)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Detalle del Aviso de Radar'
        context['parent'] = 'avisos'
        context['segment'] = 'radar'
        context['url_list'] = reverse_lazy('avisos_radares')
        return context
    
class RadarWarningPDFView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = RadarWarning
    permission_required = 'dashboard.view_radar_warning'

    def get(self, request, *args, **kwargs):
        radar_warning = self.get_object()

        # Obtener imagen del logo en formato Base64
        logo_path = os.path.join(settings.BASE_DIR, "static/dist/img/logo.png")
        logo_base64 = self.get_image_base64(logo_path)
        
        # Obtener imagen del radar_warning en Base64 si existe
        image_base64 = None
        if radar_warning.image:  # Asegúrate de que 'image' es el campo de la imagen en tu modelo
            try:
                # Obtener la ruta completa de la imagen
                image_path = radar_warning.image.path
                image_base64 = self.get_image_base64(image_path)
            except Exception as e:
                # Manejar excepción (puedes loguear el error)
                print(f"Error al cargar imagen: {e}")

        # Renderizar template HTML
        template = get_template('pages/dashboard/avisos/radares/pdf_template.html')
        context = {
            'radar_warning': radar_warning,
            'logo_base64': logo_base64,
            'image_base64': image_base64,  # Pasamos la imagen en base64 al contexto
        }
        html = template.render(context)

        # Crear PDF
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)

        if not pdf.err:
            response = HttpResponse(result.getvalue(), content_type='application/pdf')
            filename = f"aviso_radar_{radar_warning.date.strftime('%Y-%m-%d')}.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        return HttpResponse("Error al generar el PDF", status=400)

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(RadarWarning, uuid=uuid)

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