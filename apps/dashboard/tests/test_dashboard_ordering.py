import json

from django.contrib.auth.models import ContentType, User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.commercial.models import Invoice, Service, ServiceSubscription
from apps.commercial.tests.factories import (
    juridica_customer,
    make_user,
    natural_customer,
)
from apps.core.models import SiteConfiguration


def _grant(model, user, codename):
    ct = ContentType.objects.get_for_model(model)
    user.user_permissions.add(ct.permission_set.get(codename=codename))


class DashboardSubscriptionOrderTests(TestCase):
    """El panel ordena por el nombre que muestra, no por una columna vacía.

    `Customer.company_name` sólo existe para personas jurídicas: en una
    natural es NULL. Ordenar el panel por esa columna metía a todas las
    naturales al principio (SQLite) o al final (PostgreSQL) según el motor y
    dejaba el orden entre ellas al azar. La lista tiene que seguir la clave
    que el operador ve: la empresa por su nombre, la persona por su
    apellido.
    """

    @classmethod
    def setUpTestData(cls):
        SiteConfiguration.objects.get_or_create(defaults={'maintenance_mode': False})
        cls.url = reverse('dashboard:index')

        admin = User.objects.create_superuser('ordenadmin', 'orden@example.com', 'pass')
        service = Service.objects.create(
            user=admin,
            title='Svc Orden',
            summary='S',
            service_type='commercial',
            code='ORD1',
            price='50.00',
        )

        empresa = juridica_customer(company_name='AAA Empresa')
        natural = natural_customer(user=make_user('zeta', first_name='Zeta', last_name='Zeta'))

        for customer in (empresa, natural):
            ServiceSubscription.objects.create(
                customer=customer,
                service=service,
                payment_status='paid',
                start_date=timezone.now(),
            )

        # `CheckUserProfileMiddleware` manda al perfil a quien no tenga nombre
        # y apellido, así que el operador entra con los suyos.
        staff = User.objects.create_user(
            'ordenstaff',
            'staff@example.com',
            'pass',
            first_name='Staff',
            last_name='Orden',
            is_staff=True,
        )
        _grant(ServiceSubscription, staff, 'view_subscription')
        _grant(Invoice, staff, 'view_invoice')
        cls.staff = staff

    def test_el_panel_no_agrupa_a_las_naturales_por_un_campo_vacio(self):
        self.client.force_login(self.staff)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        nombres = [s['customer'] for s in json.loads(response.context['active_subs_list'])]

        # La empresa "AAA" va antes que la persona de apellido "Zeta": con
        # `company_name` NULL la natural se colaba delante en SQLite.
        self.assertLess(nombres.index('AAA Empresa'), nombres.index('Zeta Zeta'))
