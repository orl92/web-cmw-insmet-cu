import logging
import os
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from dashboard.models import CompanySettings

logger = logging.getLogger(__name__)

def enviar_correo_factura(invoice, customer, request=None, base_url=None):
    """
    Envía el correo con la factura en PDF y actualiza flags email_sent/email_error.
    Retorna True si se envió correctamente, False en caso contrario.
    """
    if not customer.user or not customer.user.email:
        return False

    # Obtener suscripción (si existe) para elegir plantilla
    first_item = invoice.items.first()
    subscription = first_item.subscription if first_item else None

    if subscription and subscription.payment_method == 'qr':
        template = 'pages/dashboard/emails/factura_qr.html'
    else:
        template = 'pages/dashboard/emails/factura.html'

    company = CompanySettings.get_instance()

    # Construir URLs base: si hay request usamos build_absolute_uri, sino BASE_URL de settings
    if base_url is None:
        if request:
            base_url = request.build_absolute_uri('/')
        else:
            base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000/')

    listado_url = base_url + reverse('listado_facturas').lstrip('/')

    context = {
        'invoice': invoice,
        'customer': customer,
        'subscription': subscription,
        'payment_method': subscription.get_payment_method_display() if subscription else '',
        'company': company,
        'index_url': base_url,
        'listado_url': listado_url,
        'current_year': timezone.now().year,
    }

    html_content = render_to_string(template, context)
    subject = f"Factura {invoice.number} - {customer.company_name}"

    email = EmailMessage(
        subject=subject,
        body=html_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[customer.user.email],
    )
    email.content_subtype = "html"

    # Adjuntar PDF si existe
    if invoice.pdf and invoice.pdf.storage.exists(invoice.pdf.name):
        with invoice.pdf.storage.open(invoice.pdf.name, 'rb') as f:
            email.attach(f'factura_{invoice.number}.pdf', f.read(), 'application/pdf')

    # Adjuntar QR si corresponde
    if subscription and subscription.payment_method == 'qr':
        from django.contrib.staticfiles import finders
        qr_path = finders.find('dist/img/QR/QR.png')
        if not qr_path:
            qr_path = os.path.join(settings.STATIC_ROOT, 'dist/img/QR/QR.png')
        if os.path.exists(qr_path):
            with open(qr_path, 'rb') as f:
                email.attach('qr_pago.png', f.read(), 'image/png')

    try:
        email.send()
        invoice.email_sent = True
        invoice.email_error = None
        invoice.save()
        logger.info(f"Factura {invoice.number} enviada a {customer.user.email}")
        return True
    except Exception as e:
        logger.error(f"Error enviando factura {invoice.number}: {e}")
        invoice.email_sent = False
        invoice.email_error = str(e)
        invoice.save()
        return False
