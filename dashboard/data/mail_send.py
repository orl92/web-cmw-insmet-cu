from datetime import datetime
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib import messages
from django.urls import reverse
from django.conf import settings


def mail_send_warning(request, object, subject, url):
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
                plain_message = strip_tags(html_message)

                email = EmailMessage(
                    subject=subject,
                    body=html_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=list(recipients),
                )
                email.content_subtype = 'html'

                # ADJUNTAR ARCHIVO PDF
                if object.file:
                    try:
                        # Obtener el nombre del archivo
                        file_name = object.file.name.split('/')[-1]  # Solo el nombre del archivo, no la ruta completa

                        # Leer el contenido del archivo
                        file_content = object.file.read()

                        # Adjuntar el archivo PDF con el tipo MIME correcto
                        email.attach(file_name, file_content, 'application/pdf')

                    except Exception as file_error:
                        # Manejar error específico del archivo sin interrumpir el envío del correo
                        messages.warning(request, f'El archivo no pudo ser adjuntado: {str(file_error)}',
                                         extra_tags='warning')
                try:
                    email.send()
                except Exception as send_error:
                    print(send_error)
                    messages.warning(request, f'Ocurrió un error al enviar el correo: {str(send_error)}',
                                     extra_tags='warning')

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
