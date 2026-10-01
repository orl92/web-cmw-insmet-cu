import contextlib
import io
import re

from django.core.exceptions import ValidationError
from PIL import Image, ImageFile

REEUP_RE = r'^\d{3}\.\d{1,2}\.\d{4,5}$'
NIT_RE = r'^\d{11}$'
ACCOUNT_RE = r'^\d{16}$'
PHONE_RE = r'^\d{8}$'
PHONE_SEPARATOR_RE = re.compile(r'[,;\s-]+')

MAX_IMAGE_UPLOAD_SIZE = 5 * 1024 * 1024  # 5 MiB
MAX_IMAGE_UPLOAD_SIZE_LABEL = '5 MiB'

INVALID_IMAGE_ERROR = (
    'El archivo no es una imagen válida o está dañada. Suba una imagen en formato PNG o JPEG.'
)
IMAGE_TOO_LARGE_ERROR = 'El archivo supera el tamaño máximo permitido de {limit}.'

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


def validate_image_upload(uploaded_file):
    """Validate an uploaded image file.

    Accepts an UploadedFile (form upload) or a File/FieldFile (already stored).
    Raises a ValidationError with an actionable message when the file is too
    large, is not an image at all, or is a corrupted image.
    """
    if uploaded_file is None:
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
