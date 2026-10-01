"""Tests for the shared image validator and the model fields that use it.

`validate_image_upload` is imported by `ProfileForm`, by the `avatar` field, and
by `SiteConfiguration.brand_logo` / `.favicon`, so it lives in `core` and is
tested from here as well as from `user_auth`. The fixtures are generated with
Pillow rather than hardcoded base64 so that every one of them is asserted to
have the property the test depends on: a fixture that is accidentally valid
makes a test pass for the wrong reason.
"""

import io
from unittest import mock

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase
from PIL import Image, ImageFile

from apps.core.models import SiteConfiguration
from apps.core.validators import (
    IMAGE_TOO_LARGE_ERROR,
    IMAGE_TOO_MANY_PIXELS_ERROR,
    INVALID_IMAGE_ERROR,
    MAX_IMAGE_PIXELS,
    MAX_IMAGE_UPLOAD_SIZE,
    strict_pillow,
    validate_image_upload,
)


def _png(size=(8, 8), color=(12, 34, 56)):
    buffer = io.BytesIO()
    Image.new('RGB', size, color).save(buffer, format='PNG')
    return buffer.getvalue()


def _idat_payload_offset(data):
    """Byte offset of the first IDAT payload byte in a PNG."""
    offset, seen_idat = 8, False
    while offset < len(data):
        length = int.from_bytes(data[offset : offset + 4], 'big')
        chunk_type = data[offset + 4 : offset + 8]
        if chunk_type == b'IDAT' and not seen_idat:
            return offset + 8, length
        seen_idat = seen_idat or chunk_type == b'IDAT'
        offset += 12 + length
    raise AssertionError('no IDAT chunk found')


def _with_corrupted_pixels():
    """A PNG whose structure is intact but whose pixel data is garbage.

    Flipping a byte inside the IDAT payload and recomputing its CRC makes
    verify() pass while load() fails, which is exactly the shape of corruption
    that used to reach storage.
    """
    import zlib

    data = bytearray(_png((64, 64)))
    payload_offset, payload_length = _idat_payload_offset(bytes(data))
    data[payload_offset + 3] ^= 0xFF

    # Recompute the CRC so the chunk is structurally valid again.
    chunk = bytes(data[payload_offset - 4 : payload_offset + payload_length])
    crc = zlib.crc32(chunk) & 0xFFFFFFFF
    data[payload_offset + payload_length : payload_offset + payload_length + 4] = crc.to_bytes(
        4, 'big'
    )
    return bytes(data)


CORRUPTED_PIXELS = _with_corrupted_pixels()


def _oversized():
    """Valid PNG over `MAX_IMAGE_UPLOAD_SIZE`; uncompressed to stay cheap."""
    buffer = io.BytesIO()
    Image.new('RGB', (1400, 1400), (10, 20, 30)).save(buffer, format='PNG', compress_level=0)
    return buffer.getvalue()


def _too_many_pixels():
    """Valid PNG that is tiny on disk but far too large to decode.

    This is the fixture that justifies `MAX_IMAGE_PIXELS`: comfortably under
    `MAX_IMAGE_UPLOAD_SIZE`, so only the pixel rule can reject it. Real pixels
    are generated rather than the header being patched, so the fixture cannot
    pass for the wrong reason.
    """
    buffer = io.BytesIO()
    Image.new('RGB', (5200, 5200), (10, 20, 30)).save(buffer, format='PNG')
    return buffer.getvalue()


OVERSIZED = _oversized()
TOO_MANY_PIXELS = _too_many_pixels()


class FixtureIntegrityTests(SimpleTestCase):
    """The fixtures must have the property each test relies on."""

    def test_corrupted_pixels_passes_verify_and_fails_load(self):
        with strict_pillow():
            Image.open(io.BytesIO(CORRUPTED_PIXELS)).verify()

            with self.assertRaises(OSError):
                Image.open(io.BytesIO(CORRUPTED_PIXELS)).load()

    def test_oversized_fixture_is_valid_and_over_the_byte_limit(self):
        with Image.open(io.BytesIO(OVERSIZED)) as image:
            image.verify()
        self.assertGreater(len(OVERSIZED), MAX_IMAGE_UPLOAD_SIZE)

    def test_too_many_pixels_fixture_is_small_on_disk_but_oversized_when_decoded(self):
        with Image.open(io.BytesIO(TOO_MANY_PIXELS)) as image:
            width, height = image.size
            image.verify()

        self.assertLessEqual(len(TOO_MANY_PIXELS), MAX_IMAGE_UPLOAD_SIZE)
        self.assertGreater(width * height, MAX_IMAGE_PIXELS)


class StrictPillowTests(SimpleTestCase):
    def test_pin_is_restored_afterwards(self):
        with mock.patch.object(ImageFile, 'LOAD_TRUNCATED_IMAGES', True):
            validate_image_upload(SimpleUploadedFile('a.png', _png()))

            self.assertTrue(ImageFile.LOAD_TRUNCATED_IMAGES)

    def test_pin_is_restored_even_when_the_image_is_rejected(self):
        with mock.patch.object(ImageFile, 'LOAD_TRUNCATED_IMAGES', True):
            with self.assertRaises(ValidationError):
                validate_image_upload(SimpleUploadedFile('a.png', CORRUPTED_PIXELS))

            self.assertTrue(ImageFile.LOAD_TRUNCATED_IMAGES)

    def test_rejects_corruption_even_when_pillow_tolerates_truncation(self):
        # weasyprint/images.py sets this at import time and the URLconf imports
        # it at boot, so without the pin the same file fails in a shell and is
        # accepted by the server.
        with (
            mock.patch.object(ImageFile, 'LOAD_TRUNCATED_IMAGES', True),
            self.assertRaises(ValidationError),
        ):
            validate_image_upload(SimpleUploadedFile('a.png', CORRUPTED_PIXELS))


class ValidateImageUploadTests(SimpleTestCase):
    def test_accepts_a_valid_upload_and_leaves_it_rewound(self):
        upload = SimpleUploadedFile('avatar.png', _png((64, 64)))

        self.assertIs(validate_image_upload(upload), upload)
        self.assertEqual(upload.tell(), 0)

    def test_returns_none_when_there_is_no_file(self):
        self.assertIsNone(validate_image_upload(None))

    def test_rejects_corrupted_pixels(self):
        with self.assertRaises(ValidationError) as ctx:
            validate_image_upload(SimpleUploadedFile('a.png', CORRUPTED_PIXELS))

        self.assertIn(INVALID_IMAGE_ERROR, ctx.exception.messages)

    def test_rejects_bytes_that_are_not_an_image(self):
        upload = SimpleUploadedFile('doc.pdf', b'%PDF-1.4 not an image', 'application/pdf')

        with self.assertRaises(ValidationError):
            validate_image_upload(upload)

    def test_rejects_a_truncated_image(self):
        data = _png((64, 64))

        with self.assertRaises(ValidationError):
            validate_image_upload(SimpleUploadedFile('a.png', data[: len(data) // 2]))

    def test_rejects_an_oversized_image(self):
        with self.assertRaises(ValidationError) as ctx:
            validate_image_upload(SimpleUploadedFile('a.png', OVERSIZED))

        self.assertIn(IMAGE_TOO_LARGE_ERROR.format(limit='5 MiB'), ctx.exception.messages)

    def test_rejects_too_many_pixels(self):
        with self.assertRaises(ValidationError) as ctx:
            validate_image_upload(SimpleUploadedFile('a.png', TOO_MANY_PIXELS))

        self.assertIn(
            IMAGE_TOO_MANY_PIXELS_ERROR.format(limit='25 megapíxeles'),
            ctx.exception.messages,
        )

    def test_rejects_too_many_pixels_before_decoding_anything(self):
        # load() is the allocation this rule exists to prevent, so the budget
        # has to be read from the header. The calls are counted instead of made
        # to raise on purpose: the validator wraps decoding in a broad
        # `except Exception` that would turn a raising stub into a
        # ValidationError, and the test would pass with the check moved after
        # load(). Counting is what pins the ordering.
        calls = []
        original_load = Image.Image.load

        def counting_load(self, *args, **kwargs):
            calls.append(self.size)
            return original_load(self, *args, **kwargs)

        with (
            mock.patch.object(Image.Image, 'load', counting_load),
            self.assertRaises(ValidationError),
        ):
            validate_image_upload(SimpleUploadedFile('a.png', TOO_MANY_PIXELS))

        self.assertEqual(calls, [], 'load() decodifico una imagen ya rechazada')

    def test_accepts_a_large_image_within_the_pixel_budget(self):
        # Guards the budget against becoming a blunt size cap. Not the
        # oversized fixture, which is over the byte limit by design.
        large_legal = _png((4000, 4000))

        self.assertIsNotNone(validate_image_upload(SimpleUploadedFile('big.png', large_legal)))


class SiteConfigurationImageFieldsTests(TestCase):
    """The branding fields carry the validator, so admin and form are both covered."""

    def setUp(self):
        self.instance = SiteConfiguration.get_instance()

    def test_valid_logo_passes_full_clean(self):
        self.instance.brand_logo = ContentFile(_png((64, 64)), name='logo.png')

        self.instance.full_clean(exclude=['favicon'])

    def test_valid_favicon_passes_full_clean(self):
        self.instance.favicon = ContentFile(_png((32, 32)), name='favicon.png')

        self.instance.full_clean(exclude=['brand_logo'])

    def test_corrupted_logo_is_rejected_by_full_clean(self):
        # full_clean() is the path the admin takes, since its ModelForm is
        # built from the model.
        self.instance.brand_logo = ContentFile(CORRUPTED_PIXELS, name='logo.png')

        with self.assertRaises(ValidationError) as ctx:
            self.instance.full_clean(exclude=['favicon'])

        self.assertIn('brand_logo', ctx.exception.error_dict)

    def test_corrupted_favicon_is_rejected_by_full_clean(self):
        self.instance.favicon = ContentFile(CORRUPTED_PIXELS, name='favicon.png')

        with self.assertRaises(ValidationError) as ctx:
            self.instance.full_clean(exclude=['brand_logo'])

        self.assertIn('favicon', ctx.exception.error_dict)

    def test_too_many_pixels_logo_is_rejected(self):
        self.instance.brand_logo = ContentFile(TOO_MANY_PIXELS, name='logo.png')

        with self.assertRaises(ValidationError) as ctx:
            self.instance.full_clean(exclude=['favicon'])

        self.assertIn('brand_logo', ctx.exception.error_dict)

    def test_fields_that_are_not_set_are_not_validated(self):
        # Both fields are null=True: leaving the branding alone must not fail.
        self.instance.full_clean()

    def test_a_broken_logo_already_on_disk_does_not_block_other_edits(self):
        # Regression guard. The validator runs on model validation, which means
        # it is handed the previously stored file when the field is untouched.
        # Rejecting that would freeze the whole settings page for anyone who
        # uploaded a damaged logo before this validator existed, with no way
        # out except re-uploading it.
        self.instance.brand_logo.save('broken-logo.png', ContentFile(CORRUPTED_PIXELS), save=True)

        self.instance.primary_color = '#112233'

        # Must not raise: the branding is not what is being edited.
        self.instance.full_clean(exclude=['favicon'])

    def test_a_stored_logo_within_budget_is_not_revalidated(self):
        self.instance.brand_logo.save('logo.png', ContentFile(_png((64, 64))), save=True)
        self.instance.primary_color = '#223344'

        self.instance.full_clean(exclude=['favicon'])
