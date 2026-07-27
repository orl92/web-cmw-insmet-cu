import os
import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import models, connection
from django.test import TransactionTestCase, override_settings

from apps.core.models import FileHandlerMixin


class SimpleFileModel(FileHandlerMixin, models.Model):
    name = models.CharField(max_length=50)
    file = models.FileField(upload_to='test/', blank=True, null=True)
    file_fields = ['file']

    class Meta:
        app_label = 'core'


class SoftDeleteFileModel(FileHandlerMixin, models.Model):
    name = models.CharField(max_length=50)
    file = models.FileField(upload_to='test/', blank=True, null=True)
    file_fields = ['file']
    record_active = models.BooleanField(default=True)

    class Meta:
        app_label = 'core'

    def delete(self, *args, **kwargs):
        if hasattr(self, '_cleanup_files'):
            self._cleanup_files()
        self.record_active = False
        self.save(update_fields=['record_active'])


MODELS = [SimpleFileModel, SoftDeleteFileModel]


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class FileHandlerTests(TransactionTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._tmp_media = tempfile.mkdtemp()
        cls._media_override = override_settings(MEDIA_ROOT=cls._tmp_media)
        cls._media_override.enable()
        cls._tables = []
        with connection.schema_editor() as schema_editor:
            for model in MODELS:
                schema_editor.create_model(model)
                cls._tables.append(model._meta.db_table)

    @classmethod
    def tearDownClass(cls):
        with connection.schema_editor() as schema_editor:
            for table in cls._tables:
                schema_editor.execute(f'DROP TABLE IF EXISTS {table}')
        cls._media_override.disable()
        shutil.rmtree(cls._tmp_media, ignore_errors=True)
        super().tearDownClass()

    def test_delete_removes_file_from_disk(self):
        pdf = SimpleUploadedFile('doc.pdf', b'%PDF-1.4', content_type='application/pdf')
        obj = SimpleFileModel.objects.create(name='test', file=pdf)
        file_path = obj.file.path
        self.assertTrue(os.path.isfile(file_path))
        obj.delete()
        self.assertFalse(os.path.isfile(file_path))

    def test_save_replaces_old_file(self):
        pdf1 = SimpleUploadedFile('v1.pdf', b'%PDF-1.4 v1', content_type='application/pdf')
        obj = SimpleFileModel.objects.create(name='test', file=pdf1)
        old_path = obj.file.path
        self.assertTrue(os.path.isfile(old_path))
        pdf2 = SimpleUploadedFile('v2.pdf', b'%PDF-1.4 v2', content_type='application/pdf')
        obj.file = pdf2
        obj.save()
        self.assertFalse(os.path.isfile(old_path))
        self.assertTrue(os.path.isfile(obj.file.path))

    def test_soft_delete_removes_file(self):
        pdf = SimpleUploadedFile('doc.pdf', b'%PDF-1.4', content_type='application/pdf')
        obj = SoftDeleteFileModel.objects.create(name='test', file=pdf)
        file_path = obj.file.path
        self.assertTrue(os.path.isfile(file_path))
        obj.delete()
        self.assertFalse(os.path.isfile(file_path))
        self.assertFalse(obj.record_active)

    def test_no_file_no_error(self):
        obj = SimpleFileModel.objects.create(name='no-file')
        obj.delete()

    def test_cleanup_files_removes_only_file_fields(self):
        pdf = SimpleUploadedFile('doc.pdf', b'%PDF-1.4', content_type='application/pdf')
        obj = SimpleFileModel.objects.create(name='test', file=pdf)
        file_path = obj.file.path
        obj._cleanup_files()
        self.assertFalse(os.path.isfile(file_path))
