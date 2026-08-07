import re

from django.core.exceptions import ValidationError

REEUP_RE = r'^\d{3}\.\d{1,2}\.\d{4,5}$'
NIT_RE = r'^\d{11}$'
ACCOUNT_RE = r'^\d{16}$'
PHONE_RE = r'^\d{8}$'
PHONE_SEPARATOR_RE = re.compile(r'[,;\s-]+')


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
