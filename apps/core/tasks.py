import logging
import os

from django.core.mail import EmailMessage

from config.huey import huey

logger = logging.getLogger(__name__)


@huey.task()
def generate_invoice_pdf_and_email_task(invoice_uuid, site_url):
    from apps.commercial.models import Invoice
    from apps.commercial.views.invoice_utils import (
        enviar_correo_factura,
        generate_invoice_pdf_standalone,
    )
    invoice = Invoice.objects.get(uuid=invoice_uuid)
    customer = invoice.customer
    items = list(invoice.items.all())

    generate_invoice_pdf_standalone(
        invoice, customer,
        invoice.subscription.start_date if invoice.subscription else invoice.issue_date,
        invoice.subscription.end_date if invoice.subscription else invoice.issue_date,
        '',
        items,
    )
    enviar_correo_factura(invoice, customer, base_url=site_url)


@huey.task()
def send_email_task(subject, html_message, from_email, recipients,
                    attachment_name=None, attachment_content=None, attachment_mime=None,
                    attachment_path=None):
    if attachment_path and os.path.isfile(attachment_path):
        attachment_name = os.path.basename(attachment_path)
        with open(attachment_path, 'rb') as f:
            attachment_content = f.read()
        attachment_mime = 'application/pdf'
    email = EmailMessage(
        subject=subject,
        body=html_message,
        from_email=from_email,
        to=list(recipients) if recipients else [],
    )
    email.content_subtype = 'html'
    if attachment_name and attachment_content and attachment_mime:
        email.attach(attachment_name, attachment_content, attachment_mime)
    try:
        email.send()
        logger.info(f'Correo enviado: {subject}')
    except Exception as e:
        logger.error(f'Error enviando correo: {e}')
