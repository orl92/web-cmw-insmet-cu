"""El detalle del contrato sigue la estética de cards de los formularios.

La vista de detalle usa las mismas cards de sección que los formularios
(`includes/dashboard/form_card.html`) y etiquetas de formulario, para que no
desentone con el resto del panel. Además ya no muestra "Registro Comercial":
el contrato no tiene ese dato (vive en `CompanySettings`), así que la fila
sólo podía imprimirse vacía.
"""

from datetime import date

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse

from apps.commercial.models import Contract, Customer
from apps.commercial.tests.factories import make_user


class ContractDetailTemplateTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        from apps.core.models import SiteConfiguration

        SiteConfiguration.objects.get_or_create(defaults={'maintenance_mode': False})
        cls.staff_user = User.objects.create_user(
            'staff.contrato', 'staff.contrato@example.com', 'pass', first_name='Sta', last_name='F'
        )
        ct = ContentType.objects.get_for_model(Contract)
        cls.staff_user.user_permissions.add(ct.permission_set.get(codename='view_contract'))
        cls.customer = Customer.objects.create(
            client_type='juridica',
            user=make_user('juridica.contrato', first_name='Empresa', last_name='S.A.'),
            company_name='Empresa Del Contrato S.A.',
            reeup='123.4.5678',
            nit='98765432101',
            account='1234567890123456',
            address='Calle 1',
            phone='71234567',
        )
        cls.contract = Contract.objects.create(
            customer=cls.customer,
            number='2026-0007',
            start_date=date(2026, 1, 1),
            validity_years=2,
        )

    def _html(self):
        self.client.force_login(self.staff_user)
        url = reverse('commercial:contrato_detail', kwargs={'uuid': self.contract.uuid})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        return response.content.decode()

    def test_muestra_los_datos_del_contrato(self):
        html = self._html()
        self.assertIn('2026-0007', html)
        self.assertIn('01/01/2026', html)
        self.assertIn('01/01/2028', html)
        self.assertIn('Empresa Del Contrato S.A.', html)

    def test_usa_las_cards_de_seccion_de_los_formularios(self):
        html = self._html()
        self.assertIn('Datos del Contrato', html)
        self.assertIn('Cliente', html)
        self.assertIn('subheader', html)
        self.assertIn('form-control-plaintext', html)

    def test_no_muestra_registro_comercial(self):
        html = self._html()
        self.assertNotIn('Registro Comercial', html)

    def test_boton_volver(self):
        html = self._html()
        self.assertIn('Volver', html)
        self.assertNotIn('Volver al Listado', html)
