"""Día SYNOP Camagüey: regla única compartida entre generación y validación.

Regla de dominio (INSMET / protocolo AAXX):
- Horas ``00`` y ``03``: la observación embebe el **día posterior**, es decir
  ``+1 día`` respecto al día actual.  EXCEPCIÓN: si la petición al API
  de estos 2 horarios se realiza en horas **anteriores a ellos**, entonces
  embebe el **día actual**.
- Los **restantes horarios** (``06/09/12/15/18/21``): **día actual**.

El "día actual" se toma en la **zona horaria local (America/Havana)**, no en
UTC: las observaciones 06-21 del día en curso se sirven con ese día, y las
SYNOP 00/03 de la madrugada siguiente se catalogan con el día +1 (el mismo
que embeben por protocolo).

Esta es la ÚNICA fuente de verdad. Tanto el generador (``views.py``, que
calcula ``obs_date``) como la validación (``GetData.get_station``, que acepta
o no la SYNOP) la importan desde aquí, de modo que generación y validación se
comportan SIEMPRE de la misma manera y es imposible que diverjan.
"""

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

POSTERIOR_HOURS = frozenset({'00', '03'})

CUBA_TZ = ZoneInfo('America/Havana')


def synop_expected_obs_date(hour: str, now: datetime | None = None) -> date:
    """Día que la SYNOP del ``hour`` debe embeker.

    ``hour`` debe ser uno de los horarios SYNOP (``00``...``21``, formato HH).
    ``now`` es el instante de referencia en cualquier zona; por defecto es la
    hora actual en ``America/Havana`` (la zona de observación).  Si ``now`` es
    *naive* se interpreta ya en hora local de Cuba.

    Devuelve el día que la SYNOP de ``hour`` debe llevar en su grupo ``YY``
    (cabecera ``AAXX YY GG``).
    """
    if now is None:
        now = datetime.now(CUBA_TZ)
    elif now.tzinfo is not None:
        now = now.astimezone(CUBA_TZ)
    if hour in POSTERIOR_HOURS:
        if now.hour < int(hour):
            return now.date()  # petición en horas anteriores → día actual
        return now.date() + timedelta(days=1)  # día posterior +1
    return now.date()  # resto de horarios → día actual
