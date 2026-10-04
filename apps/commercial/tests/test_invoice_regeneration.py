"""Regeneración de factura: la anterior sobrevive hasta que la nueva existe.

El botón "Regenerar factura" anulaba las facturas previas, borraba los
certificados y revertía la suscripción a `requested` dentro del mismo POST que
sólo redirigía al formulario de facturación. Si el staff cerraba el formulario,
la factura vieja quedaba anulada para siempre y no existía reemplazo: el
cliente perdía su comprobante y la suscripción volvía a `requested` sin ninguna
factura viva que la respaldara.

El principio que estos tests fijan:

- **Regenerar no destruye nada.** El POST sólo deja el contexto listo
  (redirige con `?regenerar=<uuid>`) y no toca facturas, certificados ni estado.
- **La anulación es consecuencia, no punto de partida.** Ocurre dentro de
  `InvoiceCreateView.form_valid`, cuando la factura nueva ya existe.
- **Abandonar el formulario no cuesta nada.** Ningún registro cambia.
- **La regeneración es de lote.** Si el staff pasa a facturación manual, la
  suscripción regenerada no se factura y por lo tanto no se anula nada: se avisa
  en vez de dejar un hueco.
"""

from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.commercial.models import (
    Certificate,
    Invoice,
    InvoiceItem,
    Service,
    ServiceSubscription,
)
from apps.commercial.tests.factories import make_user, natural_customer
from apps.core.models import SiteConfiguration
from config.huey import huey


def _make_superuser(username):
    return User.objects.create_superuser(
        username,
        f'{username}@example.com',
        'pass',
        first_name='Admin',
        last_name='Super',
    )


def _periodo(offset_days=1):
    inicio = timezone.now().date()
    return inicio.isoformat(), (inicio + timedelta(days=offset_days)).isoformat()


class RegenerarCasoBase(TestCase):
    """Suscripción pendiente de pago, con su factura y su certificado."""

    @classmethod
    def setUpTestData(cls):
        SiteConfiguration.objects.get_or_create(defaults={'maintenance_mode': False})
        cls.admin = _make_superuser('regeneraadmin')
        cls.customer = natural_customer(
            make_user('regeneracust', first_name='Ana', last_name='Norte'),
        )
        cls.service = Service.objects.create(
            user=cls.admin,
            title='Pronóstico diario',
            summary='Pronóstico puntual paraRPC',
            service_type='commercial',
            service_category='pronostico',
            code='RGN01',
            price=Decimal('45.00'),
        )
        cls.sub = ServiceSubscription.objects.create(
            customer=cls.customer,
            service=cls.service,
            quantity=10,
            payment_status='pending',
            start_date=timezone.now(),
        )
        cls.invoice_anterior = Invoice.objects.create(
            subscription=cls.sub,
            customer=cls.customer,
            number='2026-0001',
            amount=Decimal('450.00'),
        )
        InvoiceItem.objects.create(
            invoice=cls.invoice_anterior,
            subscription=cls.sub,
            codigo='RGN01',
            descripcion='Pronóstico diario',
            cantidad=Decimal('10'),
            unidad_medida='DÍA',
            precio=Decimal('45.00'),
            importe=Decimal('450.00'),
        )
        cls.certificado = Certificate.objects.create(
            subscription=cls.sub,
            pdf=SimpleUploadedFile('certificado.pdf', b'%PDF-1.4 test', 'application/pdf'),
        )
        cls.url_regenerar = reverse('commercial:factura_regenerate', args=[cls.sub.uuid])
        cls.url_crear = reverse('commercial:factura_create')

    def setUp(self):
        # El POST de facturación encola la tarea de PDF de verdad; el runner aísla
        # la cola en memoria por corrida, no por test, así que hay que vaciarla.
        huey.flush()
        self.addCleanup(huey.flush)
        self.client.force_login(self.admin)

    def _formulario(self):
        inicio, fin = _periodo()
        return {
            'customer': self.customer.pk,
            'start_date': inicio,
            'end_date': fin,
            'commercial_registry': 'REG-RGN-01',
            'subscriptions': [str(self.sub.pk)],
            'regenerar': str(self.sub.uuid),
            # La imputación a centros de costo es obligatoria: sin ella la
            # factura saldría sin el centro al que se imputa.
            'cost_allocations-TOTAL_FORMS': '1',
            'cost_allocations-INITIAL_FORMS': '0',
            'cost_allocations-MIN_NUM_FORMS': '0',
            'cost_allocations-MAX_NUM_FORMS': '1000',
            'cost_allocations-0-codigo': '700.50107',
            'cost_allocations-0-porcentaje': '100.00',
        }

    def _abrir_formulario_de_regeneracion(self):
        return self.client.get(
            self.url_crear,
            {
                'customer_uuid': str(self.customer.uuid),
                'regenerar': str(self.sub.uuid),
            },
        )

    def _mensajes(self, response):
        """Mensajes de la petición que generó `response`.

        `get_messages` lee el storage colgado del *request* (`MessageMiddleware`
        lo pone en `process_request`), no de la response: pasarle la response
        devuelve siempre una lista vacía. Además se consulta sin `follow=True`,
        porque en la petición de destino el storage ya está consumido.
        """
        return [str(m) for m in get_messages(response.wsgi_request)]


class RegenerarNoDestruyeNadaTests(RegenerarCasoBase):
    """El botón prepara el contexto; la anulación es de otro paso."""

    def test_regenerar_no_annula_la_factura_anterior(self):
        response = self.client.post(self.url_regenerar)

        self.assertEqual(response.status_code, 302)
        self.invoice_anterior.refresh_from_db()
        self.assertFalse(
            self.invoice_anterior.is_cancelled,
            'la factura se anuló antes de que existiera su reemplazo',
        )

    def test_regenerar_no_da_de_baja_los_certificados(self):
        self.client.post(self.url_regenerar)

        self.certificado.refresh_from_db()
        self.assertTrue(
            self.certificado.record_active,
            'el certificado se dio de baja antes de que existiera su reemplazo',
        )

    def test_regenerar_no_revierte_el_estado_de_la_suscripcion(self):
        self.client.post(self.url_regenerar)

        self.sub.refresh_from_db()
        self.assertEqual(self.sub.payment_status, 'pending')

    def test_regenerar_redirige_con_el_cliente_y_la_suscripcion(self):
        response = self.client.post(self.url_regenerar)

        destino = response['Location']
        self.assertIn(self.url_crear, destino)
        self.assertIn(f'customer_uuid={self.customer.uuid}', destino)
        self.assertIn(f'regenerar={self.sub.uuid}', destino)

    def test_abandonar_el_formulario_no_cambia_nada(self):
        """El recorrido completo que reportaba el operador, sin confirmar."""
        self.client.post(self.url_regenerar)
        formulario = self._abrir_formulario_de_regeneracion()
        self.assertEqual(formulario.status_code, 200)
        # El staff cierra la pestaña: no hay POST de confirmación.

        self.invoice_anterior.refresh_from_db()
        self.sub.refresh_from_db()
        self.assertFalse(self.invoice_anterior.is_cancelled)
        self.assertEqual(self.sub.payment_status, 'pending')
        self.assertEqual(
            Certificate.objects.filter(subscription=self.sub, record_active=True).count(), 1
        )
        self.assertEqual(Invoice.objects.count(), 1, 'no se creó una factura nueva')

    def test_regenerar_una_suscripcion_sin_facturas_no_annula_nada(self):
        InvoiceItem.objects.all().delete()
        # `Invoice` es `SoftDeleteModel`: `delete()` la deja en la base con
        # `record_active=False` y el manager no la filtra, así que para
        # simular que nunca existió hay que borrarla de verdad.
        for invoice in Invoice.objects.all():
            invoice.hard_delete()
        self.certificado.refresh_from_db()

        response = self.client.post(self.url_regenerar, follow=True)

        # Sin factura previa no hay nada que reemplazar: avisa y vuelve al
        # listado, pero sin haber tocado un solo registro.
        self.assertRedirects(
            response, reverse('commercial:suscripcion_list'), fetch_redirect_response=False
        )
        self.assertIn('no tiene facturas para regenerar', response.content.decode())
        self.sub.refresh_from_db()
        self.assertEqual(self.sub.payment_status, 'pending')
        self.assertTrue(self.certificado.record_active)


class FormularioDeRegeneracionTests(RegenerarCasoBase):
    """El formulario tiene que avisar qué va a pasar al guardar."""

    def test_el_formulario_avisa_que_la_factura_anterior_se_annula_al_guardar(self):
        response = self._abrir_formulario_de_regeneracion()

        self.assertContains(response, 'anulará la factura anterior')
        # Con la capital inicial: djlint parte el texto en líneas y la aserción
        # debe sobrevivir al reformateo del template.
        self.assertContains(response, 'Si cerrás el formulario ahora')

    def test_el_formulario_preselecciona_la_suscripcion_a_regenerar(self):
        response = self._abrir_formulario_de_regeneracion()

        self.assertEqual(response.context['regenerar_sub'], self.sub)
        # El pk viaja al JS que arma los checkboxes: sin esto la suscripción a
        # regenerar aparece sin marcar y el operador factura otra cosa.
        self.assertContains(response, str(self.sub.pk))

    def test_el_formulario_reenvia_la_suscripcion_al_post(self):
        response = self._abrir_formulario_de_regeneracion()

        # El campo oculto es lo que hace que el POST siga sabiendo qué
        # suscripción regenerar. Se asserta por partes porque djlint parte los
        # atributos en varias líneas y el HTML crudo nunca es contiguo.
        self.assertContains(response, 'name="regenerar"')
        self.assertContains(response, f'value="{self.sub.uuid}"')

    def test_el_formulario_sin_regenerar_no_muestra_el_aviso(self):
        response = self.client.get(self.url_crear, {'customer_uuid': str(self.customer.uuid)})

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['regenerar_sub'])

    def test_un_uuid_inexistente_no_ofrece_regenerar(self):
        response = self.client.get(
            self.url_crear,
            {
                'customer_uuid': str(self.customer.uuid),
                'regenerar': '00000000-0000-0000-0000-000000000000',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['regenerar_sub'])

    def test_una_suscripcion_pagada_no_ofrece_regenerar(self):
        self.sub.payment_status = 'paid'
        self.sub.save(update_fields=['payment_status'])

        response = self._abrir_formulario_de_regeneracion()

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['regenerar_sub'])


class ConfirmarRegeneracionTests(RegenerarCasoBase):
    """Con la factura nueva creada, la anterior sí se anula."""

    def _confirmar(self):
        return self.client.post(self.url_crear, self._formulario(), follow=True)

    def test_confirmar_crea_la_factura_nueva_y_annula_la_anterior(self):
        response = self._confirmar()

        self.assertRedirects(
            response, reverse('commercial:factura_list'), fetch_redirect_response=False
        )
        nueva = Invoice.objects.exclude(pk=self.invoice_anterior.pk).get()
        self.invoice_anterior.refresh_from_db()
        self.assertTrue(self.invoice_anterior.is_cancelled)
        self.assertFalse(nueva.is_cancelled)
        self.assertEqual(nueva.customer_id, self.customer.pk)
        self.assertEqual(nueva.amount, Decimal('450.00'))
        self.assertIn(nueva, Invoice.objects.for_subscription(self.sub))

    def test_la_factura_nueva_no_se_annula_a_si_misma(self):
        self._confirmar()

        vivas = [inv for inv in Invoice.objects.for_subscription(self.sub) if not inv.is_cancelled]
        self.assertEqual(len(vivas), 1, 'sólo puede quedar viva la factura nueva')

    def test_confirmar_da_de_baja_el_certificado_anterior(self):
        self._confirmar()

        # Baja lógica: la fila queda para la trazabilidad, pero ya no cuenta como
        # certificado vigente.
        self.assertEqual(
            Certificate.objects.filter(subscription=self.sub, record_active=True).count(), 0
        )
        self.certificado.refresh_from_db()
        self.assertFalse(self.certificado.record_active)
        self.assertIsNotNone(self.certificado.deleted_at)

    def test_confirmar_deja_la_suscripcion_pendiente_del_ciclo_nuevo(self):
        self._confirmar()

        self.sub.refresh_from_db()
        self.assertEqual(
            self.sub.payment_status,
            'pending',
            'la suscripción facturada de nuevo tiene que quedar pendiente de pago',
        )

    def test_confirmar_avisa_que_la_factura_anterior_quito_anular(self):
        # Sin `follow`: el aviso vive en los mensajes de esta petición, y en la
        # de destino el storage ya se consumió al renderizar el listado.
        response = self.client.post(self.url_crear, self._formulario())

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            any('anulada' in m.lower() for m in self._mensajes(response)),
            f'mensajes: {self._mensajes(response)}',
        )


class RegenerarEnFacturacionManualTests(RegenerarCasoBase):
    """Facturación manual: la suscripción regenerada no está en la factura."""

    def _formulario_manual(self):
        inicio, fin = _periodo()
        return {
            'customer': self.customer.pk,
            'start_date': inicio,
            'end_date': fin,
            'commercial_registry': 'REG-RGN-02',
            'regenerar': str(self.sub.uuid),
            'items-TOTAL_FORMS': '1',
            'items-INITIAL_FORMS': '0',
            'items-MIN_NUM_FORMS': '0',
            'items-MAX_NUM_FORMS': '1000',
            'items-0-service': str(self.service.pk),
            'items-0-cantidad': '5',
            'items-0-precio': '45.00',
            'items-0-unidad_medida': 'DÍA',
            'items-0-codigo': 'RGN01',
            # La imputación a centros de costo es obligatoria: una factura
            # comercial sin centro es justo el defecto que este formset impide.
            'cost_allocations-TOTAL_FORMS': '1',
            'cost_allocations-INITIAL_FORMS': '0',
            'cost_allocations-MIN_NUM_FORMS': '0',
            'cost_allocations-MAX_NUM_FORMS': '1000',
            'cost_allocations-0-codigo': '700.50107',
            'cost_allocations-0-porcentaje': '100.00',
        }

    def test_facturar_a_mano_no_annula_la_factura_anterior(self):
        self.client.post(self.url_crear, self._formulario_manual(), follow=True)

        self.invoice_anterior.refresh_from_db()
        self.assertFalse(
            self.invoice_anterior.is_cancelled,
            'la suscripción a regenerar no se facturó, así que no hay nada que reemplazar',
        )

    def test_facturar_a_mano_no_da_de_baja_el_certificado(self):
        self.client.post(self.url_crear, self._formulario_manual(), follow=True)

        self.certificado.refresh_from_db()
        self.assertTrue(self.certificado.record_active)

    def test_facturar_a_mano_avisa_que_no_se_annulo_nada(self):
        response = self.client.post(self.url_crear, self._formulario_manual())

        mensajes = self._mensajes(response)
        self.assertTrue(
            any('no se anuló' in m.lower() for m in mensajes),
            f'el operador tiene que enterarse de que no se anuló nada: {mensajes}',
        )
