"""Datos de cliente compartidos por los tests de `apps.commercial`.

El problema era el contrario al habitual en factories: los tests creaban
clientes naturales a mano con `Customer.objects.create(...)` y casi siempre con
`identity_document=None` y `agency_bank` vacío. El modelo no lo detecta (ninguno
de esos campos es NOT NULL y no hay validators para ellos), así que el registro
inválido pasaba en silencio y los listados imprimían `None`. Acá el cliente se
arma completo y se valida antes de guardarse: si falta un campo obligatorio, el
error dice cuál, en vez de dejar un `None` que se descubre tres archivos más
adelante.

`identity_document` no tiene validator en `apps/core/validators.py` (el modelo
solo impone `max_length=20`), pero la forma de 11 dígitos es la de los datos
reales y la que asumen las plantillas de factura, así que la factory la respeta
igual.
"""

import itertools
import re

from django.contrib.auth.models import User

from apps.commercial.models import Customer
from apps.core.validators import ACCOUNT_RE, NIT_RE, PHONE_RE, REEUP_RE

# Formato que asumen las plantillas de factura y los datos reales del portal.
IDENTITY_DOCUMENT_RE = re.compile(r'^\d{11}$')

# Campos sin los que un cliente natural no es identificable en ninguna pantalla.
REQUIRED_NATURAL_FIELDS = (
    'identity_document',
    'account',
    'agency_bank',
    'address',
    'phone',
)

# Contadores del proceso: cada test corre en su propia transacción, pero los
# valores se generan una sola vez y se comparten entre bases de test, así que la
# unicidad hay que garantizarla sin depender del rollback.
_seq = itertools.count(1)


class IncompleteCustomerDataError(ValueError):
    """Los datos del cliente están incompletos o mal formados.

    Se lanza antes de tocar la base de datos para que el fallo apunte al test que
    armó los datos, no a una aserción lejana que encuentra un `None`.
    """


def _seq_digits(width):
    return ''.join(str(next(_seq) % 10) for _ in range(width))


def next_account():
    """Cuenta bancaria de 16 dígitos (ver `ACCOUNT_RE`) y única en el proceso."""
    return f'9{_seq_digits(15)}'


def next_reeup():
    return f'123.{next(_seq) % 9 + 1}.{next(_seq) % 90000 + 1000:05d}'


def next_nit():
    return _seq_digits(11)


def next_identity_document():
    return f'34{_seq_digits(9)}'


def make_user(username='cliente', **overrides):
    """Usuario con nombre y apellido reales: sin ellos `display_name` cae al
    username y el perfil queda incompleto para `CheckUserProfileMiddleware`."""
    data = {
        'first_name': 'Ana',
        'last_name': 'Norte',
        'email': f'{username}@example.com',
    }
    data.update(overrides)
    return User.objects.create_user(username, **data)


def _falta(data, campos):
    return [campo for campo in campos if not str(data.get(campo) or '').strip()]


def _problemas_de_formato(data):
    problemas = []
    account = str(data.get('account') or '').strip()
    if account and not re.match(ACCOUNT_RE, account):
        problemas.append(f'account={account!r} no tiene 16 dígitos numéricos')
    reeup = str(data.get('reeup') or '').strip()
    if reeup and not re.match(REEUP_RE, reeup):
        problemas.append(f'reeup={reeup!r} no tiene el formato ###.#.####')
    nit = str(data.get('nit') or '').strip()
    if nit and not re.match(NIT_RE, nit):
        problemas.append(f'nit={nit!r} no tiene 11 dígitos numéricos')
    phone = str(data.get('phone') or '').strip(' ,;\t-')
    if phone:
        partes = [p for p in re.split(r'[,;\s-]+', phone) if p]
        if not partes or not all(re.match(PHONE_RE, parte) for parte in partes):
            problemas.append(f'phone={data["phone"]!r} no tiene teléfonos de 8 dígitos')
    identity_document = str(data.get('identity_document') or '').strip()
    if identity_document and not IDENTITY_DOCUMENT_RE.match(identity_document):
        problemas.append(f'identity_document={identity_document!r} no tiene 11 dígitos')
    return problemas


def _validar(data, campos_obligatorios):
    faltantes = _falta(data, campos_obligatorios)
    if faltantes:
        raise IncompleteCustomerDataError(
            'Faltan datos obligatorios del cliente: '
            + ', '.join(faltantes)
            + '. Usá la factory de este módulo en vez de armar el dict a mano.'
        )
    problemas = _problemas_de_formato(data)
    if problemas:
        raise IncompleteCustomerDataError(
            'Datos de cliente con formato inválido: ' + '; '.join(problemas) + '.'
        )


def natural_customer(user=None, username=None, **overrides):
    """Cliente natural completo y válido.

    `user` reutiliza un usuario que el test ya tenga (no hace falta crear un
    segundo); si no se pasa, se crea uno con nombre y apellido reales.
    """
    data = {
        'client_type': Customer.ClientType.NATURAL,
        'identity_document': next_identity_document(),
        'account': next_account(),
        'agency_bank': 'Banco Popular de Ahorro',
        'address': 'Calle del Cliente 1',
        'phone': '71234567',
    }
    data.update(overrides)
    _validar(data, REQUIRED_NATURAL_FIELDS)
    data['user'] = user or make_user(username or 'naturalcust')
    return Customer.objects.create(**data)


def juridica_customer(user=None, username=None, **overrides):
    """Cliente jurídico con los datos fiscales que exige el formulario."""
    data = {
        'client_type': Customer.ClientType.JURIDICA,
        'company_name': 'Empresa de Prueba S.A.',
        'reeup': next_reeup(),
        'nit': next_nit(),
        'account': next_account(),
        'agency_bank': 'Banco de Crédito y Comercio',
        'address': 'Avenida de la Empresa 2',
        'phone': '71234568',
    }
    data.update(overrides)
    _validar(data, ('company_name', 'account', 'agency_bank', 'address', 'phone'))
    data['user'] = user or make_user(username or 'juridcust')
    return Customer.objects.create(**data)


def valid_natural_customer():
    """Cliente natural ya existente y completo, o uno nuevo si no hay ninguno.

    Sirve para los tests que solo necesitan "un cliente": si la base del test ya
    tiene uno con los datos completos, se usa ese en lugar de crear otro.
    """
    existente = (
        Customer.objects.filter(
            client_type=Customer.ClientType.NATURAL,
            record_active=True,
        )
        .exclude(identity_document__isnull=True)
        .exclude(identity_document='')
        .select_related('user')
        .order_by('pk')
        .first()
    )
    if existente is not None and existente.user is not None:
        return existente
    return natural_customer()
