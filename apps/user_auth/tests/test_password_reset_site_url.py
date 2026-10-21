"""El enlace de restablecimiento de contraseña sale de `SITE_URL`.

Ver `odd/tasks/url-canonica-del-sitio.md`.

El host del `request` es el host por el que el operador entró: la IP del
servidor en la red interna o `localhost`. Quien recibe el correo de
restablecimiento está fuera de esa red, así que un enlace armado con ese host
no abre. `SITE_URL` es la URL pública del sitio.
"""

from unittest import mock

from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from apps.user_auth.forms.password import UserPasswordResetForm

PUBLIC_SITE_URL = 'https://cmw.insmet.cu/'
INTERNAL_HOST = '10.0.0.5:8000'
# El host interno tiene que estar permitido: si no, Django lo rechaza antes de
# que el código llegue a armar el enlace, y el test probaría el `ALLOWED_HOSTS`
# en vez del contrato de `SITE_URL`.
ALLOWED_HOSTS = ['testserver', '10.0.0.5']


class EnlaceDeRestablecimientoTests(TestCase):
    """El correo de restablecimiento lleva enlaces del sitio público."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            'resetuser',
            'resetuser@example.com',
            'pass',
            first_name='Ana',
            last_name='Norte',
        )

    def _form(self):
        request = RequestFactory().post('/user_auth/password_reset/', HTTP_HOST=INTERNAL_HOST)
        return UserPasswordResetForm(data={'email': self.user.email}, request=request)

    @override_settings(SITE_URL=PUBLIC_SITE_URL, ALLOWED_HOSTS=ALLOWED_HOSTS)
    def test_el_enlace_usa_el_host_publico_y_no_el_del_request(self):
        form = self._form()
        self.assertTrue(form.is_valid())

        contexto = {'uid': 'MQ', 'token': 'tok', 'user': self.user}
        # Se intercepta el envío de Django: lo que se verifica es el contexto
        # con el que se arma el correo, que es donde viven los enlaces.
        with mock.patch.object(PasswordResetForm, 'send_mail') as padre:
            form.send_mail(
                'registration/password_reset_subject.txt',
                'registration/password_reset_email.html',
                contexto,
                'from@example.com',
                ['to@example.com'],
            )

        ctx = padre.call_args.args[2]
        self.assertEqual(ctx['index_url'], PUBLIC_SITE_URL)
        ruta = reverse(
            'user_auth:password_reset_confirm',
            kwargs={'uidb64': 'MQ', 'token': 'tok'},
        )
        self.assertEqual(ctx['reset_url'], f'{PUBLIC_SITE_URL}{ruta.lstrip("/")}')
        self.assertNotIn(INTERNAL_HOST, ctx['index_url'])
        self.assertNotIn(INTERNAL_HOST, ctx['reset_url'])
