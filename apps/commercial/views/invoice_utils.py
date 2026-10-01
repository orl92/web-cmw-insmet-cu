import logging
import os
from functools import lru_cache

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from weasyprint import HTML

from apps.commercial.models import Contract, Customer, Invoice
from apps.core.models import CompanySettings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def require_pdf_renderer():
    """Se niega a generar un PDF sin que el motor de renderizado funcione.

    `WeasyPrint` es una biblioteca pura de Python, pero necesita la pila
    del sistema (Pango, Harfbuzz, GdkPixbuf) para convertir HTML a PDF. Si
    esa pila falta, el primer `write_pdf()` falla con un error profundo,
    no con un `ImportError` claro. Este chequeo previene que el worker
    de Huey intente generar facturas en ese estado y deja constancia de
    qué dependencias del sistema faltan, antes de tocar ningún archivo.

    Ejecuta una prueba real de renderizado (no solo una importación): al
    hacerlo una única vez por proceso (cacheado) se paga el costo de
    arranque de Pango como mucho una vez y, lo más importante, el chequeo
    ocurre ANTES de que se escriba un PDF a medio crear.
    """

    try:
        HTML(string='<p>ok</p>').write_pdf()
    except Exception as exc:
        raise RuntimeError(
            'No se puede generar el PDF de la factura: faltan bibliotecas del '
            'sistema necesarias para WeasyPrint (Pango/Harfbuzz).\n'
            '  Debian/Ubuntu: sudo apt install libpango-1.0-0 '
            'libpangoft2-1.0-0 libharfbuzz0b libgdk-pixbuf-2.0-0\n'
            '  Otras plataformas: consulte la documentación de WeasyPrint '
            'para las dependencias del sistema.'
        ) from exc


def _contrato_de_factura(invoice):
    """El contrato de la suscripción facturada, o `None`.

    `Contract.subscription` es un `OneToOneField`, así que `subscription.contract`
    lanza `Contract.DoesNotExist` cuando la suscripción todavía no tiene
    contrato: eso es un caso normal (la factura manual no tiene suscripción), no
    un error, y por eso se devuelve `None` en vez de dejar subir la excepción.
    """
    subscription = invoice.subscription if invoice else None
    if subscription is None:
        return None
    try:
        return subscription.contract
    except Contract.DoesNotExist:
        return None


def _datos_proveedor(company, contract):
    """Datos del ejecutor, con el bloque de contrato resuelto.

    El registro comercial del contrato es el más específico (es el de esa
    suscripción), así que gana; si el contrato no lo trae, se usa el de la
    empresa. Sin contrato, los tres campos quedan vacíos en vez de romper.
    """
    return {
        'nombre': company.nombre,
        'direccion': company.direccion,
        'codigo_reeup': company.codigo_reeup,
        'nit': company.nit,
        'cuenta_bancaria': company.cuenta_bancaria,
        'agencia_bancaria': company.agencia_bancaria,
        'telefonos': company.telefonos,
        'registro_comercial': (
            (contract.commercial_registry if contract else '') or company.registro_comercial
        ),
        'no_contrato': contract.number if contract else '',
        'fecha_contrato': contract.date.strftime('%d/%m/%Y') if contract else '',
    }


def _datos_cliente(customer):
    """Datos del cliente, ya resueltos según su tipo.

    La plantilla solo decide qué imprimir con `es_juridica`; qué valores van en
    cada caso se calcula acá, que es donde se puede razonar sin HTML.

    El nombre se resuelve por tipo y nunca queda en blanco: una jurídica
    imprime su razón social (es lo que imprimía antes, y es lo que va en una
    factura legal) y una persona natural su nombre, que vive en el `User`. Si
    alguno de los dos falta, se degrada al otro y, en último caso, al nombre de
    usuario. Es la misma prioridad que usa `Customer.__str__`.
    """
    if customer is None:
        return {
            'es_juridica': False,
            'nombre': '',
            'documento_identidad': '',
            'direccion': '',
            'codigo_reeup': '',
            'nit': '',
            'cuenta_bancaria': '',
            'agencia_bancaria': '',
            'telefonos': '',
        }

    es_juridica = customer.client_type == Customer.ClientType.JURIDICA
    user = customer.user
    nombre_persona = user.get_full_name() if user else ''
    if es_juridica:
        nombre = customer.company_name or nombre_persona
    else:
        nombre = nombre_persona or customer.company_name
    if not nombre and user:
        nombre = user.username

    return {
        'es_juridica': es_juridica,
        'nombre': nombre or '',
        'documento_identidad': customer.identity_document or '',
        'direccion': customer.address,
        'codigo_reeup': customer.reeup or '',
        'nit': customer.nit or '',
        'cuenta_bancaria': customer.account or '',
        'agencia_bancaria': customer.agency_bank or '',
        'telefonos': customer.phone or '',
    }


def generate_invoice_pdf_standalone(invoice, customer, start_date, end_date, items):
    company = CompanySettings.get_instance()
    periodo = f'Desde {start_date.strftime("%d/%m/%Y")} hasta {end_date.strftime("%d/%m/%Y")}'
    context = {
        'numero_factura': invoice.number,
        'fecha_facturacion': invoice.issue_date.strftime('%d de %B del %Y'),
        'periodo_facturacion': periodo,
        'cliente': _datos_cliente(customer),
        'proveedor': _datos_proveedor(company, _contrato_de_factura(invoice)),
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
    require_pdf_renderer()
    html_string = render_to_string('pages/commercial/invoice/template.html', context)
    pdf_bytes = HTML(string=html_string).write_pdf()
    filename = f'factura_{invoice.id}.pdf'
    invoice.pdf.save(filename, ContentFile(pdf_bytes))
    return pdf_bytes


def marcar_pdf(invoice, error=None):
    """Deja el estado del PDF alineado con lo que pasó en el render.

    Vive acá y no en la tarea porque hay dos caminos que generan el PDF (la
    tarea Huey y el comando de pruebas) y el estado tiene que quedar escrito
    igual en los dos.
    """
    invoice.pdf_status = Invoice.PdfStatus.FAILED if error else Invoice.PdfStatus.READY
    invoice.pdf_error = str(error) if error else None
    invoice.save(update_fields=['pdf_status', 'pdf_error'])
    return invoice


def enviar_correo_factura(invoice, customer, request=None, base_url=None):
    """
    Envía el correo con la factura en PDF y registra el resultado en
    `email_status`/`email_error`.

    Retorna True si salió, False si no. **No propaga la excepción**: quien
    llama decide si eso es un error fatal o solo un estado que hay que
    mostrar. Tragar el error acá es lo que hacía que la tarea Huey reportara
    éxito con el correo sin enviar.
    """
    if not customer.user or not customer.user.email:
        invoice.email_status = Invoice.EmailStatus.FAILED
        invoice.email_error = 'El cliente no tiene correo registrado.'
        invoice.save(update_fields=['email_status', 'email_error'])
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
        invoice.email_status = Invoice.EmailStatus.SENT
        invoice.email_error = None
        invoice.save(update_fields=['email_status', 'email_error'])
        logger.info(f'Factura {invoice.number} enviada a {customer.user.email}')
        return True
    except Exception as e:
        logger.error(f'Error enviando factura {invoice.number}: {e}')
        invoice.email_status = Invoice.EmailStatus.FAILED
        invoice.email_error = str(e)
        invoice.save(update_fields=['email_status', 'email_error'])
        return False
