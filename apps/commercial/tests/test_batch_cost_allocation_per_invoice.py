"""El reparto que declara una factura del lote es el de ESA factura.

Dos defectos de la pantalla de facturación con el mismo origen: el lote trataba
como una sola cosa lo que son varias facturas.

1. `InvoiceCreateView` construye un único formset de centros de costo y lo
   pasaba a cada factura creada. Un lote de tres solicitudes del mismo cliente
   con dos centros de costo distintos generaba tres facturas, y las tres
   quedaban imputadas a los DOS centros aunque cada una facturara servicios de
   un solo centro. El reparto es un asiento contable: atribuirle a una factura
   un centro que no le corresponde no es cosmético.

2. El borrado duro de una factura no devolvía sus suscripciones al listado:
   quedaban en `pending`, `ajax_pending_subscriptions` sólo ofrece las
   `requested`, y la solicitud desaparecía sin forma de volver a facturarla.
   Anular sí la devuelve, y el operador ve dos comportamientos distintos para lo
   que él llama "eliminar".

Los tests van contra la vista real (`InvoiceCreateView`, `InvoiceHardDeleteView`)
y contra la base, no contra la implementación interna, para que un cambio de
forma no los rompa.
"""

from datetime import datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.commercial.models import (
    Invoice,
    InvoiceItem,
    Service,
    ServiceSubscription,
)
from apps.commercial.tests.factories import natural_customer
from apps.core.models import CompanySettings, SiteConfiguration
from config.huey import huey


def _make_user(username='loteusuario', **kwargs):
    data = {
        'first_name': 'Test',
        'last_name': 'User',
        'email': f'{username}@example.com',
    }
    data.update(kwargs)
    return User.objects.create_user(username, **data)


def _make_superuser(username, **kwargs):
    email = kwargs.pop('email', f'{username}@example.com')
    data = {
        'first_name': 'Admin',
        'last_name': 'Super',
    }
    data.update(kwargs)
    return User.objects.create_superuser(username, email, 'pass', **data)


def _make_customer(username):
    """Cliente natural completo: sin contrato, la factura no exige vigencia.

    El caso real (CCS Jesús Suarez Gayol) es un cliente con datos fiscales; acá
    alcanza un natural válido porque lo que se prueba es el reparto, no la
    validación de contratos.
    """
    return natural_customer(
        _make_user(username),
        account='1234567890123456',
        agency_bank='BANDEC',
        address='Calle 10',
        phone='12345678',
    )


class RepartoPorFacturaEnElLoteTests(TestCase):
    """Un lote con varios períodos reparte cada factura con SUS centros.

    Réplica del defecto observado: 3 solicitudes del mismo cliente, 2 centros de
    costo distintos y 3 períodos distintos → 3 facturas, y cada una debe
    declarar sólo el centro de sus propios ítems al 100 %.
    """

    @classmethod
    def setUpTestData(cls):
        SiteConfiguration.objects.get_or_create(defaults={'maintenance_mode': False})
        CompanySettings.get_instance()
        cls.admin = _make_superuser('loteallocadmin')
        cls.customer = _make_customer('lotealloccust')
        cls.url = reverse('commercial:factura_create')

    def setUp(self):
        # El POST encola la tarea real de PDF: la cola se limpia en los dos
        # sentidos, como en el resto de los tests de facturación.
        huey.flush()
        self.addCleanup(huey.flush)
        self.client.force_login(self.admin)

    def _servicio(self, code, category, price):
        return Service.objects.create(
            user=self.admin,
            title=f'Servicio {code}',
            summary='Servicio de prueba',
            service_type='commercial',
            service_category=category,
            code=code,
            price=Decimal(price),
        )

    def _sub(self, service, dia, cantidad):
        return ServiceSubscription.objects.create(
            customer=self.customer,
            service=service,
            start_date=timezone.make_aware(datetime(2025, 1, dia)),
            quantity=cantidad,
            payment_status='requested',
        )

    def _post(self, subs, filas):
        datos = {
            'customer': self.customer.pk,
            'commercial_registry': 'REG-LOTE',
            'subscriptions': [str(sub.pk) for sub in subs],
            'cost_allocations-TOTAL_FORMS': str(len(filas)),
            'cost_allocations-INITIAL_FORMS': '0',
            'cost_allocations-MIN_NUM_FORMS': '0',
            'cost_allocations-MAX_NUM_FORMS': '1000',
        }
        for indice, fila in enumerate(filas):
            datos[f'cost_allocations-{indice}-codigo'] = fila['codigo']
            datos[f'cost_allocations-{indice}-porcentaje'] = fila['porcentaje']
        return self.client.post(self.url, datos)

    def _facturas_por_codigo(self):
        """Mapea el código de servicio del ítem a la factura que lo contiene."""
        return {
            item.codigo: item.invoice
            for item in InvoiceItem.objects.filter(invoice__customer=self.customer)
        }

    def _imputaciones(self, invoice):
        return [(a.codigo, a.porcentaje) for a in invoice.cost_allocations.all()]

    def test_cada_factura_del_lote_declara_solo_los_centros_de_sus_items(self):
        # Tres períodos distintos: enero-marzo, enero-febrero y sólo enero.
        # Dos centros: 700.50107 para el primer servicio y 700.50207 para los
        # otros dos, que es exactamente el caso real reportado.
        servicio_a = self._servicio('700501072507005', 'agrometeo', '100.00')
        servicio_b = self._servicio('700502072307032', 'agrometeo', '80.00')
        servicio_c = self._servicio('700502072507017', 'pronostico', '5.00')
        subs = [
            self._sub(servicio_a, 1, 3),
            self._sub(servicio_b, 28, 2),
            self._sub(servicio_c, 20, 10),
        ]

        # La pantalla deriva la UNIÓN de los centros de las marcadas, así que el
        # formset global lleva los dos y es lo que el operador acepta.
        self._post(
            subs,
            [
                {'codigo': '700.50107', 'porcentaje': '50.00'},
                {'codigo': '700.50207', 'porcentaje': '50.00'},
            ],
        )

        self.assertEqual(Invoice.objects.filter(customer=self.customer).count(), 3)
        por_codigo = self._facturas_por_codigo()

        self.assertEqual(
            self._imputaciones(por_codigo['700501072507005']),
            [('700.50107', Decimal('100.00'))],
        )
        self.assertEqual(
            self._imputaciones(por_codigo['700502072307032']),
            [('700.50207', Decimal('100.00'))],
        )
        self.assertEqual(
            self._imputaciones(por_codigo['700502072507017']),
            [('700.50207', Decimal('100.00'))],
        )

    def test_un_lote_de_un_solo_periodo_respeta_el_reparto_del_operador(self):
        """Con una sola factura, la tarjeta del operador ES su reparto."""
        servicio_a = self._servicio('700501072507005', 'agrometeo', '100.00')
        servicio_b = self._servicio('700502072307032', 'agrometeo', '80.00')
        # Mismo inicio y misma cantidad: un solo período, una sola factura.
        subs = [self._sub(servicio_a, 1, 3), self._sub(servicio_b, 1, 3)]

        self._post(
            subs,
            [
                {'codigo': '700.50107', 'porcentaje': '25.00'},
                {'codigo': '700.50207', 'porcentaje': '75.00'},
            ],
        )

        facturas = Invoice.objects.filter(customer=self.customer)
        self.assertEqual(facturas.count(), 1)
        self.assertEqual(
            self._imputaciones(facturas[0]),
            [('700.50107', Decimal('25.00')), ('700.50207', Decimal('75.00'))],
        )

    def test_una_factura_sin_codigo_derivable_no_inventa_centros(self):
        """Un código corto no aporta centro: esa factura queda sin imputación."""
        servicio_ok = self._servicio('700501072507005', 'agrometeo', '100.00')
        servicio_corto = self._servicio('123', 'agrometeo', '30.00')
        # Dos períodos distintos: enero-marzo y enero-febrero.
        subs = [self._sub(servicio_ok, 1, 3), self._sub(servicio_corto, 28, 2)]

        # Sólo el servicio con prefijo derivable aporta centro; el prefill del
        # navegador manda esa única fila al 100 %.
        self._post(subs, [{'codigo': '700.50107', 'porcentaje': '100.00'}])

        self.assertEqual(Invoice.objects.filter(customer=self.customer).count(), 2)
        por_codigo = self._facturas_por_codigo()

        self.assertEqual(
            self._imputaciones(por_codigo['700501072507005']),
            [('700.50107', Decimal('100.00'))],
        )
        self.assertEqual(self._imputaciones(por_codigo['123']), [])


class BorradoDuroLiberaLaSuscripcionTests(TestCase):
    """Borrar una factura devuelve sus suscripciones al listado del lote.

    El borrado duro se lleva los ítems y con ellos el vínculo, así que la
    liberación tiene que ocurrir antes. Una suscripción ya pagada no se toca.
    """

    @classmethod
    def setUpTestData(cls):
        SiteConfiguration.objects.get_or_create(defaults={'maintenance_mode': False})
        CompanySettings.get_instance()
        cls.admin = _make_superuser('harddeladmin')

    def _factura_con_suscripcion(self, estado):
        customer = _make_customer(f'harddelcust-{estado}')
        servicio = Service.objects.create(
            user=self.admin,
            title='Servicio a borrar',
            summary='Servicio de prueba',
            service_type='commercial',
            service_category='pronostico',
            code='700501072507005',
            price=Decimal('45.00'),
        )
        sub = ServiceSubscription.objects.create(
            customer=customer,
            service=servicio,
            start_date=timezone.now(),
            quantity=2,
            payment_status=estado,
        )
        invoice = Invoice.objects.create(
            customer=customer,
            number=f'HD-{estado}',
            amount=Decimal('90.00'),
        )
        InvoiceItem.objects.create(
            invoice=invoice,
            subscription=sub,
            codigo=servicio.code,
            descripcion=servicio.title,
            cantidad=2,
            precio=Decimal('45.00'),
            importe=Decimal('90.00'),
        )
        return invoice, sub

    def test_borrado_duro_devuelve_la_suscripcion_pendiente_a_solicitado(self):
        factura, sub = self._factura_con_suscripcion('pending')
        self.client.force_login(self.admin)

        self.client.post(reverse('commercial:factura_delete', args=[factura.uuid]))

        sub.refresh_from_db()
        self.assertEqual(sub.payment_status, 'requested')

    def test_borrado_duro_no_toca_una_suscripcion_pagada(self):
        factura, sub = self._factura_con_suscripcion('paid')
        self.client.force_login(self.admin)

        self.client.post(reverse('commercial:factura_delete', args=[factura.uuid]))

        sub.refresh_from_db()
        self.assertEqual(sub.payment_status, 'paid')
