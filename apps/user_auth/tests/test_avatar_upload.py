"""Avatar upload validation tests.

`Profile.save()` re-encodes the avatar with Pillow, which forces a full decode
of the file, so a corrupted upload used to surface as an HTTP 500 instead of a
form error. Coverage is split in two layers:

* the form and the view turn a bad upload into a field error (user visible);
* `Profile.save()` never raises, whatever is already on disk (robustness).

Fixtures are generated with Pillow instead of hardcoded base64 on purpose: a
mangled literal stays invisible until something decodes it, and a fixture that
is accidentally valid makes a test pass for the wrong reason. Every corruption
below is asserted to be corrupt before being relied upon.
"""

import io
import os
import tempfile
import zlib
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from PIL import Image, ImageFile

from apps.core.validators import (
    INVALID_IMAGE_ERROR,
    MAX_IMAGE_UPLOAD_SIZE,
    strict_pillow,
    validate_image_upload,
)
from apps.user_auth.forms.profile import ProfileForm
from apps.user_auth.models import Profile

User = get_user_model()

PDF_BYTES = b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<< /Type /Catalog >>\nendobj\n'


def _png_bytes(size=(8, 8), color=(12, 34, 56)):
    """Bytes of a valid PNG generated with Pillow."""
    buffer = io.BytesIO()
    Image.new('RGB', size, color).save(buffer, format='PNG')
    return bytearray(buffer.getvalue())


def _idat_chunk(data):
    """Return (payload_offset, length) of the first IDAT chunk."""
    offset = 8  # skip the PNG signature
    while offset < len(data):
        length = int.from_bytes(data[offset : offset + 4], 'big')
        if data[offset + 4 : offset + 8] == b'IDAT':
            return offset + 8, length
        offset += 12 + length
    raise AssertionError('El PNG fixture no tiene chunk IDAT.')


def _png_with_broken_pixels():
    """PNG with intact structure but garbage pixel data.

    The IDAT checksum is recomputed after flipping a byte, so `verify()`
    accepts the file and only `load()` rejects it. This is exactly the file
    that used to reach `Profile.save()` and raise `OSError` (500): a check
    based on `verify()` alone would not catch it.

    `load()` only raises while `ImageFile.LOAD_TRUNCATED_IMAGES` is False, so
    every consumer of this fixture runs inside `strict_pillow()`.
    """
    data = _png_bytes((64, 64))
    payload_offset, length = _idat_chunk(data)
    payload = bytearray(data[payload_offset : payload_offset + length])
    payload[length - 40] ^= 0xFF
    data[payload_offset : payload_offset + length] = payload
    crc = zlib.crc32(b'IDAT' + bytes(payload)) & 0xFFFFFFFF
    data[payload_offset + length : payload_offset + length + 4] = crc.to_bytes(4, 'big')
    return bytes(data)


def _png_with_broken_structure():
    """PNG with a damaged IDAT checksum: `verify()` raises SyntaxError."""
    data = _png_bytes()
    payload_offset, _ = _idat_chunk(data)
    data[payload_offset + 3] ^= 0xFF
    return bytes(data)


def _oversized_png():
    """A perfectly valid PNG that is bigger than `MAX_IMAGE_UPLOAD_SIZE`.

    Generated without compressing so it stays cheap: the point of the fixture
    is a real, decodable image that only the size rule may reject.
    """
    buffer = io.BytesIO()
    Image.new('RGB', (1400, 1400), (10, 20, 30)).save(buffer, format='PNG', compress_level=0)
    return buffer.getvalue()


OVERSIZED_PNG_BYTES = _oversized_png()


def _upload(name, data, content_type='image/png'):
    return SimpleUploadedFile(name, data, content_type)


def _profile_form_data(first_name='Nombre', last_name='Apellido', email='user@example.com'):
    return {
        'first_name': first_name,
        'last_name': last_name,
        'email': email,
        'newsletter': '',
    }


class AvatarFixtureIntegrityTests(SimpleTestCase):
    """The fixtures must be broken on purpose, otherwise every test below lies."""

    def test_valid_png_fixture_is_valid(self):
        image = Image.open(io.BytesIO(_png_bytes((640, 480))))
        image.verify()

    def test_broken_pixels_fixture_passes_verify_and_fails_load(self):
        data = _png_with_broken_pixels()

        with strict_pillow():
            Image.open(io.BytesIO(data)).verify()  # structure is intact

            with self.assertRaises(OSError):
                Image.open(io.BytesIO(data)).load()

    def test_broken_structure_fixture_fails_verify(self):
        with self.assertRaises(SyntaxError):
            Image.open(io.BytesIO(_png_with_broken_structure())).verify()

    def test_oversized_fixture_is_a_valid_but_large_image(self):
        data = OVERSIZED_PNG_BYTES
        image = Image.open(io.BytesIO(data))
        image.verify()
        image.close()

        self.assertGreater(len(data), MAX_IMAGE_UPLOAD_SIZE)


class ValidateImageUploadTests(SimpleTestCase):
    def test_accepts_a_valid_upload_and_rewinds_it(self):
        upload = _upload('avatar.png', bytes(_png_bytes((64, 64))))

        self.assertIs(validate_image_upload(upload), upload)
        self.assertEqual(upload.tell(), 0)

    def test_rejects_broken_pixels(self):
        with self.assertRaises(ValidationError) as ctx:
            validate_image_upload(_upload('broken.png', _png_with_broken_pixels()))

        self.assertIn(INVALID_IMAGE_ERROR, ctx.exception.messages)

    def test_rejects_broken_pixels_even_when_pillow_is_set_to_tolerate_truncation(self):
        # weasyprint/images.py sets LOAD_TRUNCATED_IMAGES = True at import time,
        # and the URLconf imports it at boot: without pinning the flag, a broken
        # pixel stream is silently accepted in production while the very same
        # file raises in a shell. The validator must not depend on that order.
        with (
            mock.patch.object(ImageFile, 'LOAD_TRUNCATED_IMAGES', True),
            self.assertRaises(ValidationError),
        ):
            validate_image_upload(_upload('broken.png', _png_with_broken_pixels()))

    def test_restores_the_truncation_flag_afterwards(self):
        with mock.patch.object(ImageFile, 'LOAD_TRUNCATED_IMAGES', True):
            validate_image_upload(_upload('avatar.png', bytes(_png_bytes())))
            self.assertTrue(ImageFile.LOAD_TRUNCATED_IMAGES)

    def test_rejects_broken_structure(self):
        with self.assertRaises(ValidationError):
            validate_image_upload(_upload('broken.png', _png_with_broken_structure()))

    def test_rejects_a_truncated_image(self):
        data = bytes(_png_bytes((64, 64)))
        with self.assertRaises(ValidationError):
            validate_image_upload(_upload('truncated.png', data[: len(data) // 2]))

    def test_rejects_bytes_that_are_not_an_image(self):
        with self.assertRaises(ValidationError):
            validate_image_upload(_upload('doc.pdf', PDF_BYTES, 'application/pdf'))

    def test_rejects_an_oversized_image(self):
        with self.assertRaises(ValidationError):
            validate_image_upload(_upload('huge.png', OVERSIZED_PNG_BYTES))

    def test_returns_none_for_a_missing_file(self):
        self.assertIsNone(validate_image_upload(None))


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class ProfileFormAvatarTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('avatarform', 'avatarform@example.com', 'password')
        cls.user.first_name = 'Nombre'
        cls.user.last_name = 'Apellido'
        cls.user.save()

    def _form(self, files=None, data=None, instance=None):
        return ProfileForm(
            data=data if data is not None else _profile_form_data(),
            files=files or {},
            instance=instance if instance is not None else self.user.profile,
        )

    def test_valid_image_is_saved_and_processed(self):
        form = self._form(files={'avatar': _upload('avatar.png', bytes(_png_bytes((640, 480))))})

        self.assertTrue(form.is_valid(), form.errors)
        profile = form.save()
        profile.refresh_from_db()

        self.assertTrue(profile.avatar)
        self.assertTrue(os.path.isfile(profile.avatar.path))
        with Image.open(profile.avatar.path) as image:
            self.assertEqual(image.size, (300, 300))

    def test_non_image_file_is_a_field_error(self):
        # Django's own forms.ImageField rejects this one first (its verify()
        # pass raises UnidentifiedImageError), so the message shown here is
        # Django's; the shared validator covers the same ground for callers
        # that bypass the form field (see ValidateImageUploadTests).
        form = self._form(files={'avatar': _upload('doc.pdf', PDF_BYTES, 'application/pdf')})

        self.assertFalse(form.is_valid())
        self.assertIn('avatar', form.errors)
        self.assertFalse(Profile.objects.get(user=self.user).avatar)

    def test_oversized_image_is_a_field_error(self):
        form = self._form(files={'avatar': _upload('huge.png', OVERSIZED_PNG_BYTES)})

        self.assertFalse(form.is_valid())
        self.assertIn('avatar', form.errors)
        self.assertIn('5 MiB', form.errors['avatar'][0])

    def test_broken_pixels_are_reported_by_the_shared_validator(self):
        form = self._form(files={'avatar': _upload('broken.png', _png_with_broken_pixels())})

        self.assertFalse(form.is_valid())
        self.assertIn('avatar', form.errors)
        # The message comes from apps.core.validators, not from Django's own
        # ImageField: its verify() pass accepts this file.
        self.assertIn(INVALID_IMAGE_ERROR, form.errors['avatar'])

    def test_existing_broken_avatar_does_not_block_other_fields(self):
        profile = self.user.profile
        profile.avatar.save('broken.png', ContentFile(_png_with_broken_pixels()), save=False)
        with self.assertLogs('apps.user_auth.models', level='ERROR'):
            profile.save()

        form = self._form(
            data=_profile_form_data(first_name='Nuevo'),
            instance=profile,
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.assertNotIn('avatar', form.errors)
        form.save()
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Nuevo')


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class ProfileSaveRobustnessTests(TestCase):
    """`save()` must never turn a broken file into a 500, whoever calls it."""

    def setUp(self):
        self.user = User.objects.create_superuser(
            'avatarmodel', 'avatarmodel@example.com', 'password'
        )

    def test_save_with_a_broken_avatar_on_disk_does_not_raise(self):
        profile = self.user.profile
        broken = _png_with_broken_pixels()
        profile.avatar.save('broken.png', ContentFile(broken), save=False)

        with self.assertLogs('apps.user_auth.models', level='ERROR') as logs:
            profile.save()  # must not raise

        self.assertIn('avatar', logs.output[0])
        self.assertEqual(profile.avatar.read(), broken)

    def test_save_with_a_broken_structure_avatar_on_disk_does_not_raise(self):
        profile = self.user.profile
        broken = _png_with_broken_structure()
        profile.avatar.save('broken.png', ContentFile(broken), save=False)

        with self.assertLogs('apps.user_auth.models', level='ERROR'):
            profile.save()  # must not raise

        self.assertEqual(profile.avatar.read(), broken)

    def test_avatar_is_left_untouched_when_processing_fails(self):
        profile = self.user.profile
        broken = _png_with_broken_pixels()
        profile.avatar.save('broken.png', ContentFile(broken), save=False)
        with self.assertLogs('apps.user_auth.models', level='ERROR'):
            profile.save()

        with open(profile.avatar.path, 'rb') as stored:
            self.assertEqual(stored.read(), broken)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class ProfileUpdateViewAvatarTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(
            'avatarview', 'avatarview@example.com', 'password'
        )
        self.user.first_name = 'Nombre'
        self.user.last_name = 'Apellido'
        self.user.email = 'avatarview@example.com'
        self.user.save()
        self.url = reverse('user_auth:profile_update')

    def test_corrupted_png_returns_a_field_error_instead_of_an_exception(self):
        self.client.force_login(self.user)

        response = self.client.post(
            self.url,
            {
                'first_name': 'Nombre',
                'last_name': 'Apellido',
                'email': 'avatarview@example.com',
                'avatar': _upload('broken.png', _png_with_broken_pixels()),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('avatar', response.context['form'].errors)
        self.assertEqual(response.context['active_tab'], 'personal')
        self.assertFalse(Profile.objects.get(user=self.user).avatar)

    def test_valid_png_saves_the_processed_avatar(self):
        self.client.force_login(self.user)

        response = self.client.post(
            self.url,
            {
                'first_name': 'Nombre',
                'last_name': 'Apellido',
                'email': 'avatarview@example.com',
                'avatar': _upload('avatar.png', bytes(_png_bytes((640, 480)))),
            },
            follow=True,
        )

        self.assertRedirects(response, reverse('user_auth:profile_detail'))
        profile = Profile.objects.get(user=self.user)
        self.assertTrue(os.path.isfile(profile.avatar.path))
        with Image.open(profile.avatar.path) as image:
            self.assertEqual(image.size, (300, 300))
