import logging
import os

from django.core.mail import EmailMessage

from config.huey import huey

logger = logging.getLogger(__name__)

# Tres reintentos con espera creciente: 30 s, 60 s y 120 s, o sea unos 3,5 min de
# cobertura para un fallo transitorio (SMTP caído, disco lleno, sin render).
# El backoff tiene que ser un NÚMERO: huey multiplica la espera por él en cada
# reintento, así que `True` es un no-op silencioso (30 * True == 30).
RETRY_POLICY = {'retries': 3, 'retry_delay': 30, 'retry_backoff': 2}


@huey.task(**RETRY_POLICY)
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
        invoice,
        customer,
        invoice.subscription.start_date if invoice.subscription else invoice.issue_date,
        invoice.subscription.end_date if invoice.subscription else invoice.issue_date,
        '',
        items,
    )
    enviar_correo_factura(invoice, customer, base_url=site_url)


@huey.task(**RETRY_POLICY)
def send_email_task(
    subject,
    html_message,
    from_email,
    recipients,
    attachment_name=None,
    attachment_content=None,
    attachment_mime=None,
    attachment_path=None,
):
    if attachment_path and os.path.isfile(attachment_path):
        if not attachment_name:
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
    email.send()
    logger.info(f'Correo enviado: {subject}')
