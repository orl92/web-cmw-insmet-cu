"""El listado de clientes no puede dejar un `None` donde va un dato fiscal.

`Customer.reeup` y `Customer.nit` son opcionales: una persona jurídica sin
datos fiscales registrados los tenía como NULL, y la plantilla los imprimía
literalmente como `None`. La convención del propio listado ya era el guion
largo para el dato ausente.
"""

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse

from apps.commercial.models import Customer
from apps.commercial.tests.factories import make_user


class CustomerListFiscalDataTests(TestCase):
    """Los datos fiscales ausentes se muestran como guion, no como `None`."""

    @classmethod
    def setUpTestData(cls):
        from apps.core.models import SiteConfiguration

        SiteConfiguration.objects.get_or_create(defaults={'maintenance_mode': False})
        cls.staff_user = User.objects.create_user(
            'staff.fiscal',
            'staff.fiscal@example.com',
            'pass',
            first_name='Sta',
            last_name='F',
        )
        ct = ContentType.objects.get_for_model(Customer)
        cls.staff_user.user_permissions.add(ct.permission_set.get(codename='view_customer'))
        cls.url = reverse('commercial:cliente_list')

    def _html(self):
        self.client.force_login(self.staff_user)
        return self.client.get(self.url).content.decode()

    def test_juridica_sin_datos_fiscales_muestra_guion(self):
        Customer.objects.create(
            client_type='juridica',
            user=make_user('juridica.sin.fiscal', first_name='Empresa', last_name='S.A.'),
            company_name='Empresa Sin Fiscal S.A.',
        )
        html = self._html()
        self.assertIn('Empresa Sin Fiscal S.A.', html)
        self.assertNotIn('>None</div>', html)

    def test_juridica_con_datos_fiscales_muestra_los_valores(self):
        Customer.objects.create(
            client_type='juridica',
            user=make_user('juridica.con.fiscal', first_name='Empresa', last_name='S.A.'),
            company_name='Empresa Con Fiscal S.A.',
            reeup='123.4.5678',
            nit='987654321',
        )
        html = self._html()
        self.assertIn('123.4.5678', html)
        self.assertIn('987654321', html)
        self.assertNotIn('>None</div>', html)
