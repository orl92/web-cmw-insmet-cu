from django.contrib.auth.models import User
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from apps.core.models import SiteConfiguration
from apps.meteo.models import Warning as MeteoWarning

WARNING_VIEWS = (
    ('early', 'home:warnings_early'),
    ('storm', 'home:warnings_storm'),
    ('tropical_cyclone', 'home:warnings_tropical'),
)


def _render_count(client, url):
    """Render the warning URL and return it plus the total SQL query count."""
    with CaptureQueriesContext(connection) as queries:
        response = client.get(url)
    return len(queries), response


class PublicWarningNoNPlusOneTests(TestCase):
    """Regression guard for the public warning views (012-n1-avisos-publicos).

    Each view queryset must join both the author User and its Profile via a
    single select_related('user', 'user__profile') JOIN so that accessing
    warning.user / warning.user.profile does not issue extra per-warning
    queries. Assert the total query count is constant as the warning count
    grows (no linear growth).
    """

    @classmethod
    def setUpTestData(cls):
        SiteConfiguration.objects.update_or_create(defaults={'maintenance_mode': False})
        cls.url = {wt: reverse(name) for wt, name in WARNING_VIEWS}

    @staticmethod
    def _create_user(username, index):
        return User.objects.create_user(
            username,
            f'{username}@example.com',
            'pass',
            first_name='Nombre',
            last_name=f'Apellido{index}',
        )

    @staticmethod
    def _create_warning(warning_type, user, summary):
        return MeteoWarning.objects.create(
            warning_type=warning_type,
            user=user,
            summary=summary,
            valid_until=timezone.now() + timezone.timedelta(days=1),
        )

    def test_query_count_is_constant_as_warnings_grow(self):
        """Rendering the list must not issue queries linear in warning count."""
        for warning_type, _ in WARNING_VIEWS:
            user = self._create_user(f'{warning_type}_author', 1)
            self._create_warning(warning_type, user, 'Único aviso')

            count_one, _ = _render_count(self.client, self.url[warning_type])
            self.assertGreater(count_one, 0)

            # Seed N extra warnings (each with its own User + auto-created Profile).
            for i in range(2, 12):
                u = self._create_user(f'{warning_type}_author_{i}', i)
                self._create_warning(warning_type, u, f'Aviso {i}')

            count_n, response = _render_count(self.client, self.url[warning_type])

            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                count_n,
                count_one,
                msg=(
                    f'Query count grew for warning_type={warning_type}: '
                    f'{count_one} -> {count_n}. N+1 likely via user__profile.'
                ),
            )


class PublicWarningRenderTests(TestCase):
    """The pages must still render the author correctly (no regression)."""

    @classmethod
    def setUpTestData(cls):
        SiteConfiguration.objects.update_or_create(defaults={'maintenance_mode': False})
        cls.users = {}
        for warning_type, _ in WARNING_VIEWS:
            user = User.objects.create_user(
                f'author_{warning_type}',
                f'{warning_type}@example.com',
                'pass',
                first_name='Nombre',
                last_name='Renderizado',
            )
            cls.users[warning_type] = user
            MeteoWarning.objects.create(
                warning_type=warning_type,
                user=user,
                summary=f'Aviso {warning_type}',
                valid_until=timezone.now() + timezone.timedelta(days=1),
            )

    def test_views_render_author(self):
        for warning_type, name in WARNING_VIEWS:
            with self.subTest(warning_type=warning_type):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 200)
                user = self.users[warning_type]
                # The author full name is rendered on the page.
                self.assertContains(response, user.get_full_name())
