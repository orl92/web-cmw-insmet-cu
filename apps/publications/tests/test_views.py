from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from apps.core.models import SiteConfiguration
from apps.publications.models import Author, ScientificPublication


def _make_superuser(username, **kwargs):
    email = kwargs.pop('email', f'{username}@example.com')
    data = {'first_name': 'Admin', 'last_name': 'Super'}
    data.update(kwargs)
    return User.objects.create_superuser(username, email, 'pass', **data)


def disable_maintenance_mode():
    SiteConfiguration.objects.get_or_create(defaults={'maintenance_mode': False})


def _pdf(name='paper.pdf'):
    return SimpleUploadedFile(name, b'%PDF-1.4 test content', content_type='application/pdf')


class ScientificPublicationCreateViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        disable_maintenance_mode()
        cls.admin = _make_superuser('pubadmin')
        cls.url = reverse('publications:create')

    def _valid_data(self):
        return {
            'title': 'Publicación de prueba',
            'publication_date': '2026-05-10',
            'summary': 'Resumen de prueba',
            'pdf': _pdf(),
            'author_first_name': 'Autor',
            'author_last_name': 'Principal',
            'author_email': 'autor@example.com',
            'author_institution': 'CMP Camagüey',
            'author_orcid_id': '0000-0001-2345-6789',
            'coauthors-TOTAL_FORMS': '1',
            'coauthors-INITIAL_FORMS': '0',
            'coauthors-MIN_NUM_FORMS': '0',
            'coauthors-MAX_NUM_FORMS': '1000',
            'coauthors-0-first_name': 'Coautor',
            'coauthors-0-last_name': 'Secundario',
            'coauthors-0-email': 'coautor@example.com',
            'coauthors-0-institution': 'Universidad',
            'coauthors-0-orcid_id': '0000-0002-0000-0000',
        }

    def test_get_returns_200_and_renders_fieldsets(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Coautores (Opcional)')
        self.assertContains(response, 'id="add-coauthor"')
        self.assertContains(response, 'id="coauthors-table-body-desktop"')

    def test_get_does_not_reload_jquery_cdn_or_dead_script(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'code.jquery.com')
        self.assertNotContains(response, 'syncIndices')

    def test_post_creates_publication_with_coauthors(self):
        self.client.force_login(self.admin)
        self.client.post(self.url, self._valid_data(), follow=True)
        pub = ScientificPublication.objects.filter(title='Publicación de prueba').first()
        self.assertIsNotNone(pub)
        self.assertEqual(pub.coauthors.count(), 1)
        self.assertTrue(
            Author.objects.filter(first_name='Coautor', last_name='Secundario').exists()
        )


class ScientificPublicationUpdateViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        disable_maintenance_mode()
        cls.admin = _make_superuser('pubadmin2')
        cls.author = Author.objects.create(
            first_name='Autor',
            last_name='Principal',
            email='autor@example.com',
            institution='CMP Camagüey',
        )
        cls.coauthor = Author.objects.create(
            first_name='Coautor',
            last_name='Secundario',
            email='coautor@example.com',
        )
        cls.pub = ScientificPublication.objects.create(
            author=cls.author,
            title='Publicación a editar',
            publication_date='2026-05-10',
            summary='Resumen',
            pdf=_pdf(),
        )
        cls.pub.coauthors.add(cls.coauthor)
        cls.url = reverse('publications:update', args=[cls.pub.uuid])

    def _valid_data(self):
        return {
            'title': 'Publicación a editar',
            'publication_date': '2026-05-10',
            'summary': 'Resumen',
            'pdf': _pdf(),
            'author_first_name': 'Autor',
            'author_last_name': 'Principal',
            'author_email': 'autor@example.com',
            'author_institution': 'CMP Camagüey',
            'author_orcid_id': '',
            'coauthors-TOTAL_FORMS': '1',
            'coauthors-INITIAL_FORMS': '1',
            'coauthors-MIN_NUM_FORMS': '0',
            'coauthors-MAX_NUM_FORMS': '1000',
            'coauthors-0-id': str(self.coauthor.pk),
            'coauthors-0-first_name': 'Coautor',
            'coauthors-0-last_name': 'Secundario',
            'coauthors-0-email': 'coautor@example.com',
            'coauthors-0-institution': '',
            'coauthors-0-orcid_id': '',
        }

    def test_get_renders_existing_coauthor_values(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'coauthors-0-first_name')
        self.assertContains(response, 'value="Coautor"')

    def test_get_prepopulates_publication_date(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="10/05/2026"')

    def test_invalid_post_keeps_submitted_date(self):
        self.client.force_login(self.admin)
        data = self._valid_data()
        data['title'] = ''
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="10/05/2026"')

    def test_post_preserves_coauthor(self):
        self.client.force_login(self.admin)
        self.client.post(self.url, self._valid_data(), follow=True)
        self.assertEqual(self.pub.coauthors.count(), 1)
        self.assertEqual(self.pub.coauthors.first().pk, self.coauthor.pk)

    def test_post_with_delete_flag_drops_coauthor(self):
        self.client.force_login(self.admin)
        data = self._valid_data()
        data['coauthors-0-DELETE'] = 'on'
        self.client.post(self.url, data, follow=True)
        self.assertEqual(self.pub.coauthors.count(), 0)


class ScientificPublicationDetailViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        disable_maintenance_mode()
        cls.admin = _make_superuser('pubadmin3')
        cls.author = Author.objects.create(
            first_name='Autor',
            last_name='Principal',
            email='autor@example.com',
            institution='CMP Camagüey',
        )
        cls.coauthor = Author.objects.create(
            first_name='Coautor',
            last_name='Secundario',
            email='coautor@example.com',
        )
        cls.pub = ScientificPublication.objects.create(
            author=cls.author,
            title='Publicación detalle',
            publication_date='2026-05-10',
            summary='Resumen de detalle',
            pdf=_pdf('articulo_final.pdf'),
        )
        cls.pub.coauthors.add(cls.coauthor)
        cls.url = reverse('publications:detail', args=[cls.pub.uuid])

    def test_get_renders_detail_200(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Publicación detalle')
        self.assertContains(response, 'Autor Principal')
        self.assertContains(response, 'Coautores')
        self.assertContains(response, 'Coautor Secundario')

    def test_detail_renders_clean_filename_not_full_path(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url)
        self.assertContains(response, 'articulo_final.pdf')
        self.assertContains(response, 'Ver PDF')
        self.assertContains(
            response,
            reverse('publications:pdf', args=[self.pub.uuid]),
        )

    def test_detail_does_not_show_usuario_item(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url)
        self.assertNotContains(response, 'datagrid-title">Usuario</div>')
