import contextlib
import io
import re

from django.core.exceptions import ValidationError
from django.db.models.fields.files import FieldFile
from PIL import Image, ImageFile

REEUP_RE = r'^\d{3}\.\d{1,2}\.\d{4,5}$'
NIT_RE = r'^\d{11}$'
ACCOUNT_RE = r'^\d{16}$'
PHONE_RE = r'^\d{8}$'
PHONE_SEPARATOR_RE = re.compile(r'[,;\s-]+')

MAX_IMAGE_UPLOAD_SIZE = 5 * 1024 * 1024  # 5 MiB
MAX_IMAGE_UPLOAD_SIZE_LABEL = '5 MiB'

# The byte limit above does NOT bound memory use: a PNG of a flat colour
# compresses to almost nothing and expands enormously. Measured in this repo,
# a 13000x13000 PNG is 0.51 MiB on disk — comfortably under MAX_IMAGE_UPLOAD_SIZE
# — and still needs ~645 MiB of RAM to decode, taking 6+ seconds of CPU. Pillow's
# own DecompressionBombError only fires at 178 MP, far too late to be a guard.
#
# So the real limit is the decoded pixel count, checked from the header BEFORE
# any decoding happens, which is why the size is read and not the pixels.
# 25 MP is ~100 MiB as RGBA: far above any sane avatar or logo, far below what
# takes a worker down.
MAX_IMAGE_PIXELS = 25_000_000
MAX_IMAGE_PIXELS_LABEL = '25 megapíxeles'

INVALID_IMAGE_ERROR = (
    'El archivo no es una imagen válida o está dañada. Suba una imagen en formato PNG o JPEG.'
)
IMAGE_TOO_LARGE_ERROR = 'El archivo supera el tamaño máximo permitido de {limit}.'
IMAGE_TOO_MANY_PIXELS_ERROR = (
    'La imagen es demasiado grande: {limit}. Redimensione la imagen antes de subirla.'
)

# Pillow does not report every kind of corruption with the same exception, and
# three of them do NOT inherit from OSError, so they have to be listed
# explicitly or they escape as an HTTP 500: `SyntaxError` (broken PNG
# checksum), `ValueError` and `Image.DecompressionBombError`.
# `PIL.UnidentifiedImageError` inherits from `OSError`, so it is already
# covered here (listing it again would be flagged as redundant by ruff B014).
PILLOW_ERRORS = (OSError, SyntaxError, ValueError, Image.DecompressionBombError)


def validate_reeup(value):
    if value and not re.match(REEUP_RE, value):
        raise ValidationError('El REEUP debe tener el formato ###.#.#### o ###.##.#####')
    return value


def validate_nit(value):
    if value and not re.match(NIT_RE, value):
        raise ValidationError('El NIT debe tener exactamente 11 dígitos numéricos.')
    return value


def validate_account(value):
    if value and not re.match(ACCOUNT_RE, value):
        raise ValidationError('La cuenta bancaria debe tener exactamente 16 dígitos numéricos.')
    return value


def validate_phones(value):
    if not value:
        return value
    value = value.strip(' ,;\t-')
    phones = [phone for phone in PHONE_SEPARATOR_RE.split(value) if phone]
    if not phones or not all(re.match(PHONE_RE, phone) for phone in phones):
        raise ValidationError(
            'Cada teléfono debe tener exactamente 8 dígitos numéricos. '
            'Separe varios teléfonos por coma, espacio o guión.'
        )
    return value


def _rewind(file_object):
    """Rewind a file-like object to the start, if it is seekable."""
    if not (hasattr(file_object, 'seek') and callable(file_object.seek)):
        return
    with contextlib.suppress(Exception):
        file_object.seek(0)


def _file_size(file_object):
    """Return the size in bytes, or None when it cannot be determined."""
    try:
        return file_object.size
    except Exception:
        # FieldFile.size raises when the file is missing from the storage.
        return None


def _read_bytes(file_object):
    """Read the whole content, rewinding first so the offset never matters."""
    _rewind(file_object)
    try:
        return file_object.read()
    except Exception as exc:
        raise ValidationError(INVALID_IMAGE_ERROR) from exc


def _check_pixel_budget(size):
    """Reject an image whose decoded size exceeds MAX_IMAGE_PIXELS.

    `size` comes straight from the image header, so this runs without decoding
    a single pixel. That matters: the failure mode being prevented is the
    memory allocation, and `Image.load()` is what performs it.
    """
    width, height = size
    if width * height > MAX_IMAGE_PIXELS:
        raise ValidationError(IMAGE_TOO_MANY_PIXELS_ERROR.format(limit=MAX_IMAGE_PIXELS_LABEL))


@contextlib.contextmanager
def strict_pillow():
    """Force Pillow to reject damaged pixel data instead of padding it.

    `PIL.ImageFile.LOAD_TRUNCATED_IMAGES` is a process-wide flag, and WeasyPrint
    flips it to True when it is imported (`weasyprint/images.py` does it at module
    level). Since a Django server loads the URLconf at boot, that flag is already
    True by the time any request runs, and with it `Image.load()` silently accepts
    a PNG whose pixel stream is broken: the same file raises in a shell and is
    accepted in production. Pinning the flag for the duration of the Pillow call
    keeps the validation and the avatar processing deterministic instead of
    dependent on the module import order.

    Not thread-safe by nature (the flag is global), and deliberately so: the only
    effect of a race is that a concurrent load() elsewhere is strict or lenient
    for the few microseconds this block takes.
    """
    previous = ImageFile.LOAD_TRUNCATED_IMAGES
    ImageFile.LOAD_TRUNCATED_IMAGES = False
    try:
        yield
    finally:
        ImageFile.LOAD_TRUNCATED_IMAGES = previous


def _is_stored_file(candidate):
    """True when the file is an ImageField value already persisted on disk.

    Model validation (`full_clean`) hands the validator whatever the field holds,
    which for an untouched field is the previously stored file rather than a new
    upload. Validating that would be actively harmful: a branding file uploaded
    before this validator existed would make every later edit to the settings
    page impossible to save, with no way out except re-uploading it.

    Existence in storage is the test rather than `FieldFile._committed`: that
    attribute is private, has no public property, and is True from `__init__`
    even for a file that was assigned but never written.
    """
    if not isinstance(candidate, FieldFile) or not candidate.name:
        return False

    try:
        return candidate.storage.exists(candidate.name)
    except Exception:
        # A storage backend that cannot answer must not turn an ordinary
        # upload into a skip. Assume it is new and validate it.
        return False


def validate_image_upload(uploaded_file):
    """Validate an uploaded image file.

    Accepts an UploadedFile (form upload) or a File/FieldFile (already stored).
    Raises a ValidationError with an actionable message when the file is too
    large, declares too many pixels, is not an image at all, or is corrupted.

    The two limits are not redundant and neither is enough alone: MAX_IMAGE_UPLOAD_SIZE
    bounds the upload, MAX_IMAGE_PIXELS bounds the memory it turns into.

    A file that is already stored and unchanged is skipped: this validates
    uploads, not storage. See `_is_stored_file`.
    """
    if uploaded_file is None:
        return uploaded_file

    if _is_stored_file(uploaded_file):
        return uploaded_file

    size = _file_size(uploaded_file)
    if size is not None and size > MAX_IMAGE_UPLOAD_SIZE:
        raise ValidationError(IMAGE_TOO_LARGE_ERROR.format(limit=MAX_IMAGE_UPLOAD_SIZE_LABEL))

    # Pillow gets a private copy of the bytes: reading it must not leave the
    # original pointer somewhere in the middle for whoever saves the file next.
    data = _read_bytes(uploaded_file)

    # Two passes are required, and neither one alone is enough:
    # verify() reads the structure (chunk checksums) but leaves the image object
    # unusable, and load() decodes the pixel data that verify() never inspects.
    # So verify() is followed by a fresh open() plus load().
    with strict_pillow():
        # Reject on the declared dimensions first, before anything is decoded:
        # load() is what allocates the memory, so this is the only check that
        # actually prevents the allocation rather than complaining afterwards.
        try:
            with Image.open(io.BytesIO(data)) as image:
                _check_pixel_budget(image.size)
        except ValidationError:
            raise
        except Exception as exc:
            raise ValidationError(INVALID_IMAGE_ERROR) from exc

        for stage in ('verify', 'load'):
            try:
                with Image.open(io.BytesIO(data)) as image:
                    getattr(image, stage)()
            except Exception as exc:
                # PILLOW_ERRORS names the failure modes Pillow documents
                # (UnidentifiedImageError, truncated reads, bad checksum,
                # decompression bomb); the bare Exception is the net so that no
                # internal error (struct, zlib, unknown format key...) escapes
                # as an HTTP 500 either.
                raise ValidationError(INVALID_IMAGE_ERROR) from exc

    # The caller may still have to store the file: leave it readable from the start.
    _rewind(uploaded_file)

    return uploaded_file
