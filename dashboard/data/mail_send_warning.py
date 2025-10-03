from datetime import datetime
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib import messages
from django.urls import reverse
from django.conf import settings


def mail_send_warning(request, object, subject):
    # Construir la URL dinámica"
    listado_url = request.build_absolute_uri(reverse('alerta_temprana'))
    index_url = request.build_absolute_uri(reverse('index'))
    # image_url = self.request.build_absolute_uri(self.object.file.url)

    # Obtener la lista seleccionada en el formulario
    recipient_list = object.email_recipient_list

    if recipient_list:
        recipients = recipient_list.recipients.values_list('email', flat=True)

        if recipients:
            # Enviar correo
            try:
                subject = subject
                html_message = render_to_string(
                    'pages/dashboard/emails/notification.html',
                    {
                        'alert': object,
                        'listado_url': listado_url,  # Pasa la URL al contexto del correo
                        'index_url': index_url,  # URL al índice de la página
                        # 'image_url': image_url,
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
                email.content_subtype = 'html'  # Asegura que el correo se envíe como HTML
                email.send()

                # Mostrar mensaje de éxito para el envío del correo
                messages.success(request, 'El correo de notificación ha sido enviado con éxito.',
                                 extra_tags='success')
            except Exception as e:
                # Manejar errores de envío
                messages.error(request, f'Ocurrió un error al enviar el correo: {str(e)}', extra_tags='danger')
        else:
            messages.warning(request, 'La lista de correos seleccionada no tiene destinatarios.',
                             extra_tags='warning')
    else:
        messages.warning(request, 'No se seleccionó ninguna lista de correos para esta actualización.',
                         extra_tags='warning')