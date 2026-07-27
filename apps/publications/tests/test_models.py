from datetime import date

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from apps.core.tests.base import FileHandlingTestCase
from apps.publications.models import Author, ScientificPublication


class AuthorTests(TestCase):
    def test_create_author(self):
        author = Author.objects.create(
            first_name='Juan', last_name='Perez',
            email='juan@example.com', institution='UCLV',
            orcid_id='0000-0001-2345-6789',
        )
        self.assertEqual(str(author), 'Juan Perez')
        self.assertIsNotNone(author.uuid)

    def test_author_ordering(self):
        Author.objects.create(first_name='Ana', last_name='Zulu')
        Author.objects.create(first_name='Luis', last_name='Beta')
        authors = Author.objects.all()
        self.assertEqual(authors[0].last_name, 'Beta')
        self.assertEqual(authors[1].last_name, 'Zulu')

    def test_author_blank_fields(self):
        author = Author.objects.create(first_name='Maria', last_name='Lopez')
        self.assertIsNone(author.email)
        self.assertEqual(author.institution, '')
        self.assertEqual(author.orcid_id, '')


class ScientificPublicationTests(FileHandlingTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = Author.objects.create(first_name='Carlos', last_name='Garcia')

    def test_create_publication(self):
        pdf = SimpleUploadedFile('test.pdf', b'%PDF-1.4 test', content_type='application/pdf')
        pub = ScientificPublication.objects.create(
            title='Estudio del Clima',
            author=self.author,
            publication_date=date(2024, 6, 15),
            summary='Resumen del estudio',
            pdf_file=pdf,
        )
        self.assertEqual(str(pub), 'Estudio del Clima')
        self.assertIsNotNone(pub.uuid)
        self.assertIsNotNone(pub.created_at)
        self.assertIsNotNone(pub.updated_at)

    def test_publication_ordering(self):
        pdf = SimpleUploadedFile('p.pdf', b'%PDF-1.4', content_type='application/pdf')
        pub1 = ScientificPublication.objects.create(
            title='Primera', author=self.author,
            publication_date=date(2024, 1, 1), summary='S1', pdf_file=pdf,
        )
        pub2 = ScientificPublication.objects.create(
            title='Segunda', author=self.author,
            publication_date=date(2024, 6, 1), summary='S2', pdf_file=pdf,
        )
        pubs = ScientificPublication.objects.all()
        self.assertEqual(pubs[0], pub2)
        self.assertEqual(pubs[1], pub1)

    def test_file_fields_defined(self):
        self.assertEqual(ScientificPublication.file_fields, ['pdf_file'])

    def test_custom_permissions(self):
        meta = ScientificPublication._meta
        perms = {p[0] for p in meta.permissions}
        expected = {
            'view_scientific_publication',
            'add_scientific_publication',
            'change_scientific_publication',
            'delete_scientific_publication',
        }
        self.assertEqual(perms, expected)
        self.assertEqual(meta.default_permissions, ())

    def test_author_verbose_names(self):
        meta = Author._meta
        perms = {p[0] for p in meta.permissions}
        expected = {
            'view_author', 'add_author', 'change_author', 'delete_author',
        }
        self.assertEqual(perms, expected)
        self.assertEqual(meta.default_permissions, ())
