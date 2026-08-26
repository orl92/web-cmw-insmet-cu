import re
from datetime import date, datetime, time

from django import template

register = template.Library()


@register.filter(name='add_class')
def add_class(value, css_class):
    return value.as_widget(attrs={'class': css_class})


@register.filter(name='add_attrs')
def add_attrs(value, attrs_str):
    pairs = attrs_str.split(',')
    attrs = {}
    for pair in pairs:
        key, val = pair.split(':', 1)
        attrs[key.strip()] = val.strip()
    return value.as_widget(attrs=attrs)


@register.filter(name='with_invalid')
def with_invalid(value):
    if value.errors:
        attrs = {'class': f'{value.field.widget.attrs.get("class", "")} is-invalid'.strip()}
        return value.as_widget(attrs=attrs)
    return value


@register.filter
def filename(value):
    if not value:
        return ''
    name = value.name.split('/')[-1]
    return re.sub(r'^[0-9a-f-]{36}_', '', name)


@register.filter(name='fmt_date')
def fmt_date(value):
    """Formatea date/datetime/ISO-string a dd/mm/aaaa."""
    date_val = _coerce_date(value)
    if date_val is None:
        return value if isinstance(value, str) else ''
    return date_val.strftime('%d/%m/%Y')


@register.filter
def iso_date(value):
    if isinstance(value, date):
        return value.strftime('%Y-%m-%d')
    return value


@register.filter
def fmt_datetime(value):
    if isinstance(value, datetime):
        return value.strftime('%d/%m/%Y %I:%M %p')
    dt = _coerce_datetime(value)
    if dt is None:
        return value if isinstance(value, str) else ''
    return dt.strftime('%d/%m/%Y %I:%M %p')


@register.filter
def iso_datetime(value):
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%dT%H:%M')
    return value


@register.filter
def to_time_value(value):
    """Valor 12h (hh:mm AM/PM) para el picker de hora; normaliza el string ya enviado.

    En la carga inicial el valor es un objeto time/datetime -> 'hh:mm AM/PM', que
    Tempus (modo time, locale 'en') parsea con el formato 'hh:mm T'. Tras un error
    de validación el valor ya es el string enviado: si es parseable (12h o 24h) se
    normaliza a 12h AM/PM; si no, se respeta tal cual. Django lo parsea con %I:%M %p.
    """
    if value in (None, ''):
        return ''
    if isinstance(value, (datetime, time)):
        return value.strftime('%I:%M %p')
    s = str(value).strip()
    for fmt in ('%I:%M %p', '%I:%M%p', '%H:%M'):
        try:
            return datetime.strptime(s, fmt).strftime('%I:%M %p')
        except ValueError:
            continue
    return s


def _coerce_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return datetime.strptime(value, '%Y-%m-%d').date()
        except ValueError:
            return None
    return None


def _coerce_datetime(value):
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        for fmt in ('%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M'):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
    return None
