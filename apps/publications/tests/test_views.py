from datetime import date

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from apps.dashboard.models import SiteConfiguration
from apps.publications.models import Author, ScientificPublication


def _make_admin(username='admin', **kwargs):
    email = kwargs.pop('email', f'{username}@example.com')
    data = {'first_name': 'Admin', 'last_name': 'User'}
    data.update(kwargs)
    return User.objects.create_superuser(username, email, 'password', **data)


def _disable_maintenance():
    SiteConfiguration.objects.get_or_create(defaults={'maintenance_mode': False})


class ScientificPublicationListViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        _disable_maintenance()
        cls.admin = _make_admin('pubadmin')
        cls.url = reverse('publications:list')
        cls.author = Author.objects.create(first_name='Ana', last_name='Lopez')
        pdf = SimpleUploadedFile('p.pdf', b'%PDF-1.4', content_type='application/pdf')
        cls.pub = ScientificPublication.objects.create(
            title='Test Pub', author=cls.author,
            publication_date=date(2024, 6, 1), summary='Sum', pdf_file=pdf,
        )

    def test_login_required(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_superuser_can_access(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_list_contains_publications(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url)
        self.assertContains(response, 'Test Pub')

    def test_list_context(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url)
        self.assertIn('objects', response.context)
        self.assertEqual(response.context['objects'].count(), 1)


class ScientificPublicationCreateViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        _disable_maintenance()
        cls.admin = _make_admin('pubcreate')
        cls.url = reverse('publications:create')
        cls.author = Author.objects.create(first_name='Luis', last_name='Mesa')

    def test_login_required(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_superuser_can_access(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_create_publication(self):
        self.client.force_login(self.admin)
        pdf = SimpleUploadedFile('new.pdf', b'%PDF-1.4 new', content_type='application/pdf')
        data = {
            'title': 'Nueva Publicacion',
            'publication_date': '2024-07-01',
            'summary': 'Resumen nuevo',
            'pdf_file': pdf,
            'author_first_name': 'Maria',
            'author_last_name': 'Torres',
            'author_email': 'maria@example.com',
            'author_institution': 'UCLV',
            'author_orcid_id': '',
            'coauthors-TOTAL_FORMS': '0',
            'coauthors-INITIAL_FORMS': '0',
            'coauthors-MIN_NUM_FORMS': '0',
            'coauthors-MAX_NUM_FORMS': '1000',
        }
        response = self.client.post(self.url, data, follow=True)
        self.assertTrue(ScientificPublication.objects.filter(title='Nueva Publicacion').exists())
        self.assertRedirects(response, reverse('publications:list'))

    def test_create_requires_author_name(self):
        self.client.force_login(self.admin)
        pdf = SimpleUploadedFile('bad.pdf', b'%PDF-1.4', content_type='application/pdf')
        data = {
            'title': 'No Author Name',
            'publication_date': '2024-07-01',
            'summary': 'Missing author name',
            'pdf_file': pdf,
            'author_first_name': '',
            'author_last_name': '',
            'author_email': '',
            'author_institution': '',
            'author_orcid_id': '',
            'coauthors-TOTAL_FORMS': '0',
            'coauthors-INITIAL_FORMS': '0',
            'coauthors-MIN_NUM_FORMS': '0',
            'coauthors-MAX_NUM_FORMS': '1000',
        }
        response = self.client.post(self.url, data, follow=True)
        self.assertFalse(ScientificPublication.objects.filter(title='No Author Name').exists())


class ScientificPublicationUpdateViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        _disable_maintenance()
        cls.admin = _make_admin('pubupdate')
        cls.author = Author.objects.create(first_name='Original', last_name='Author')
        pdf = SimpleUploadedFile('orig.pdf', b'%PDF-1.4 orig', content_type='application/pdf')
        cls.pub = ScientificPublication.objects.create(
            title='Original Title', author=cls.author,
            publication_date=date(2024, 1, 1), summary='Original', pdf_file=pdf,
        )
        cls.url = reverse('publications:update', args=[cls.pub.uuid])

    def test_login_required(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_superuser_can_access(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_update_publication(self):
        self.client.force_login(self.admin)
        pdf = SimpleUploadedFile('updated.pdf', b'%PDF-1.4 updated', content_type='application/pdf')
        data = {
            'title': 'Updated Title',
            'publication_date': '2024-06-15',
            'summary': 'Updated summary',
            'pdf_file': pdf,
            'author_first_name': 'Original',
            'author_last_name': 'Author',
            'author_email': '',
            'author_institution': '',
            'author_orcid_id': '',
            'coauthors-TOTAL_FORMS': '0',
            'coauthors-INITIAL_FORMS': '0',
            'coauthors-MIN_NUM_FORMS': '0',
            'coauthors-MAX_NUM_FORMS': '1000',
        }
        response = self.client.post(self.url, data, follow=True)
        self.pub.refresh_from_db()
        self.assertEqual(self.pub.title, 'Updated Title')
        self.assertRedirects(response, reverse('publications:list'))


class ScientificPublicationDeleteViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        _disable_maintenance()
        cls.admin = _make_admin('pubdelete')
        cls.author = Author.objects.create(first_name='Delete', last_name='Me')
        pdf = SimpleUploadedFile('del.pdf', b'%PDF-1.4 del', content_type='application/pdf')
        cls.pub = ScientificPublication.objects.create(
            title='Delete Me', author=cls.author,
            publication_date=date(2024, 1, 1), summary='To be deleted', pdf_file=pdf,
        )
        cls.url = reverse('publications:delete', args=[cls.pub.uuid])

    def test_login_required(self):
        self.client.logout()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)

    def test_delete_publication(self):
        self.client.force_login(self.admin)
        response = self.client.post(self.url, follow=True)
        self.assertFalse(ScientificPublication.objects.filter(pk=self.pub.pk).exists())
        self.assertRedirects(response, reverse('publications:list'))


class ScientificPublicationDetailViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        _disable_maintenance()
        cls.admin = _make_admin('pubdetail')
        cls.author = Author.objects.create(first_name='Detail', last_name='View')
        pdf = SimpleUploadedFile('det.pdf', b'%PDF-1.4 det', content_type='application/pdf')
        cls.pub = ScientificPublication.objects.create(
            title='Detail View Test', author=cls.author,
            publication_date=date(2024, 1, 1), summary='Detail', pdf_file=pdf,
        )
        cls.url = reverse('publications:detail', args=[cls.pub.uuid])

    def test_login_required(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_superuser_can_access(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_detail_contains_publication(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url)
        self.assertContains(response, 'Detail View Test')
