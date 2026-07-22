import os

from django.contrib.admin.models import LogEntry
from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.common.utils import (
    get_img_path,
    get_moon_img_path,
    get_sun_img_path,
    log_action,
    pdf_upload_path,
    image_upload_path,
)


class GetImgPathTests(SimpleTestCase):
    def test_known_code_without_variation_returns_base_image(self):
        path = get_img_path('N', 'morning')
        self.assertIn('nublado.png', path)

    def test_known_code_with_variation_returns_period_image(self):
        path = get_img_path('PN', 'morning')
        self.assertIn('poco_nublado_m.png', path)

    def test_unknown_code_returns_empty_string(self):
        path = get_img_path('INVALID_CODE')
        self.assertEqual(path, '')

    def test_default_period_is_afternoon(self):
        path = get_img_path('AIS CHUB')
        self.assertIn('aislados_chubascos_a.png', path)


class GetMoonImgPathTests(SimpleTestCase):
    def test_known_phase_returns_path(self):
        path = get_moon_img_path('Luna Nueva')
        self.assertIn('new_moon.png', path)

    def test_unknown_phase_returns_empty(self):
        path = get_moon_img_path('Fase Inexistente')
        self.assertEqual(path, '')


class GetSunImgPathTests(SimpleTestCase):
    def test_sunrise_returns_path(self):
        path = get_sun_img_path('sunrise')
        self.assertIn('sunrise.png', path)

    def test_sunset_returns_path(self):
        path = get_sun_img_path('sunset')
        self.assertIn('sunset.png', path)

    def test_unknown_event_returns_empty(self):
        path = get_sun_img_path('nonexistent')
        self.assertEqual(path, '')


def _make_mock_instance(class_name='testmodel'):
    cls = type(class_name, (object,), {
        '__module__': 'apps.common.tests.test_utils',
    })
    return type('MockInstance', (), {'__class__': cls})()


class PdfUploadPathTests(SimpleTestCase):
    def test_generates_correct_path_format(self):
        instance = _make_mock_instance('mymodel')
        filename = 'test document.pdf'
        path = pdf_upload_path(instance, filename)
        self.assertTrue(path.startswith('pdf/mymodel/'))
        self.assertTrue(path.endswith('_test_document.pdf'))
        uuid_part = path.split('/')[2].split('_')[0]
        self.assertEqual(len(uuid_part), 36)


class ImageUploadPathTests(SimpleTestCase):
    def test_generates_correct_path_format(self):
        instance = _make_mock_instance('mymodel')
        filename = 'photo.jpg'
        path = image_upload_path(instance, filename)
        self.assertTrue(path.startswith('img/mymodel/'))
        self.assertTrue(path.endswith('_photo.jpg'))


class LogActionTests(TestCase):
    def test_log_action_creates_log_entry(self):
        user = User.objects.create_user('testuser', 'test@example.com', 'password')
        model_instance = User.objects.create_user('target', 'target@example.com', 'password')
        log_action(user, model_instance, 1, 'Test message')
        self.assertEqual(LogEntry.objects.count(), 1)
        entry = LogEntry.objects.first()
        self.assertEqual(entry.user, user)
        self.assertEqual(entry.action_flag, 1)
        self.assertEqual(entry.change_message, 'Test message')


def _make_minimal_png():
    """Genera un PNG válido mínimo de 1x1 pixel."""
    import struct
    import zlib

    def chunk(chunk_type, data):
        c = chunk_type + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)

    signature = b'\x89PNG\r\n\x1a\n'
    ihdr = chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0))
    raw_data = b'\x00\xff\x00\x00'  # filter byte + RGB
    idat = chunk(b'IDAT', zlib.compress(raw_data))
    iend = chunk(b'IEND', b'')
    return signature + ihdr + idat + iend


class FileHandlerMixinTests(TestCase):
    def test_profile_avatar_upload_and_cleanup(self):
        from django.contrib.auth.models import User
        user = User.objects.create_user('filetest2', 'file2@example.com', 'password')
        profile = user.profile
        png_content = _make_minimal_png()
        uploaded = SimpleUploadedFile('avatar_test.png', png_content, content_type='image/png')
        profile.avatar = uploaded
        profile.save()
        avatar_path = profile.avatar.path
        self.assertTrue(os.path.exists(avatar_path))
        self.assertGreater(os.path.getsize(avatar_path), 0)
        profile.delete()
        self.assertFalse(os.path.exists(avatar_path))
