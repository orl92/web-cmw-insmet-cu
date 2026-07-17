from datetime import datetime
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib import messages
from django.urls import reverse
from django.conf import settings

from dashboard.tasks import send_email_task


def mail_send(request, object, subject, url):
    # Construir la URL dinámica
    listado_url = request.build_absolute_uri(reverse(f'{url}'))
    index_url = request.build_absolute_uri(reverse('index'))

    # Obtener la lista seleccionada en el formulario
    recipient_list = object.email_recipient_list

    if recipient_list:
        recipients = recipient_list.recipients.values_list('email', flat=True)

        if recipients:
            try:
                subject = subject
                html_message = render_to_string(
                    'pages/dashboard/emails/notification.html',
                    {
                        'alert': object,
                        'listado_url': listado_url,
                        'index_url': index_url,
                        'current_year': datetime.now().year
                    }
                )

                attachment_name = None
                attachment_content = None
                attachment_mime = None
                if object.file:
                    try:
                        file_name = object.file.name.split('/')[-1]
                        file_content = object.file.read()
                        attachment_name = file_name
                        attachment_content = file_content
                        attachment_mime = 'application/pdf'
                    except Exception as file_error:
                        messages.warning(request, f'El archivo no pudo ser adjuntado: {str(file_error)}',
                                         extra_tags='warning')

                recipients_list = list(recipients)
                send_email_task(
                    subject,
                    html_message,
                    settings.DEFAULT_FROM_EMAIL,
                    recipients_list,
                    attachment_name=attachment_name,
                    attachment_content=attachment_content,
                    attachment_mime=attachment_mime,
                )
                messages.success(request, 'El correo de notificación ha sido enviado con éxito.',
                                 extra_tags='success')
            except Exception as e:
                messages.error(request, f'Ocurrió un error al enviar el correo: {str(e)}', extra_tags='danger')
        else:
            messages.warning(request, 'La lista de correos seleccionada no tiene destinatarios.',
                             extra_tags='warning')
    else:
        messages.warning(request, 'No se seleccionó ninguna lista de correos para esta actualización.',
                         extra_tags='warning')
