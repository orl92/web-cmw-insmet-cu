import logging
import os

import pdfkit
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from apps.core.models import CompanySettings

logger = logging.getLogger(__name__)


def generate_invoice_pdf_standalone(
    invoice, customer, start_date, end_date, commercial_registry, items
):
    company = CompanySettings.get_instance()
    periodo = f'Desde {start_date.strftime("%d/%m/%Y")} hasta {end_date.strftime("%d/%m/%Y")}'
    context = {
        'numero_factura': invoice.number,
        'fecha_facturacion': invoice.issue_date.strftime('%d de %B del %Y'),
        'periodo_facturacion': periodo,
        'cliente': {
            'nombre': customer.company_name,
            'direccion': customer.address,
            'codigo_reeup': customer.reeup or '',
            'nit': customer.nit or '',
            'cuenta_bancaria': customer.account or '',
            'agencia_bancaria': customer.agency_bank or '',
            'telefonos': customer.phone or '',
        },
        'proveedor': {
            'nombre': company.nombre,
            'direccion': company.direccion,
            'codigo_reeup': company.codigo_reeup,
            'nit': company.nit,
            'cuenta_bancaria': company.cuenta_bancaria,
            'agencia_bancaria': company.agencia_bancaria,
            'telefonos': company.telefonos,
            'registro_comercial': commercial_registry,
            'no_contrato': '',
            'fecha_contrato': '',
        },
        'items': [
            {
                'codigo': item.codigo,
                'descripcion': item.descripcion,
                'cantidad': item.cantidad,
                'unidad_medida': item.unidad_medida,
                'precio': item.precio,
                'importe': item.importe,
            }
            for item in items
        ],
        'total': float(invoice.amount),
        'current_year': timezone.now().year,
    }
    html_string = render_to_string('pages/commercial/invoice/factura_template.html', context)
    options = {
        'page-size': 'A4',
        'margin-top': '10mm',
        'margin-bottom': '10mm',
        'margin-left': '10mm',
        'margin-right': '10mm',
        'encoding': 'UTF-8',
        'no-outline': None,
        'enable-local-file-access': None,
    }
    pdf_bytes = pdfkit.from_string(html_string, False, options=options)
    filename = f'factura_{invoice.id}.pdf'
    invoice.pdf.save(filename, ContentFile(pdf_bytes))


def enviar_correo_factura(invoice, customer, request=None, base_url=None):
    """
    Envía el correo con la factura en PDF y actualiza flags email_sent/email_error.
    Retorna True si se envió correctamente, False en caso contrario.
    """
    if not customer.user or not customer.user.email:
        return False

    first_item = invoice.items.first()
    subscription = first_item.subscription if first_item else None

    if subscription and subscription.payment_method == 'qr':
        template = 'pages/commercial/emails/factura_qr.html'
    else:
        template = 'pages/commercial/emails/factura.html'

    company = CompanySettings.get_instance()

    if base_url is None:
        if request:
            base_url = request.build_absolute_uri('/')
        else:
            base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000/')

    listado_url = base_url + reverse('commercial:factura_list').lstrip('/')

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
    subject = f'Factura {invoice.number} - {customer.company_name}'

    email = EmailMessage(
        subject=subject,
        body=html_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[customer.user.email],
    )
    email.content_subtype = 'html'

    if invoice.pdf and invoice.pdf.storage.exists(invoice.pdf.name):
        with invoice.pdf.storage.open(invoice.pdf.name, 'rb') as f:
            email.attach(
                f'factura_{invoice.number}_{invoice.issue_date:%Y-%m-%d}.pdf',
                f.read(),
                'application/pdf',
            )

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
        logger.info(f'Factura {invoice.number} enviada a {customer.user.email}')
        return True
    except Exception as e:
        logger.error(f'Error enviando factura {invoice.number}: {e}')
        invoice.email_sent = False
        invoice.email_error = str(e)
        invoice.save()
        return False
