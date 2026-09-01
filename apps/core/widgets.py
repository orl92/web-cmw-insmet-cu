import datetime

from django.forms import DateTimeInput


class TempusAwareDateTimeInput(DateTimeInput):
    """DateTime input that always renders the meridiem as English ``AM``/``PM``.

    Tempus Dominus is configured with ``locale='en'`` for datetime pickers and
    writes the value as ``dd/MM/yyyy hh:mm AM/PM`` (see ``static/dist/js/tempus-init.js``
    -> ``canonicalFormat``). Django's default render uses ``strftime('%p')``, which under
    a Spanish OS locale yields ``a. m.``/``p. m.`` and breaks Tempus' parsing on edit
    (the field shows only "a"). Rendering English AM/PM keeps the initial value
    consistent with both Tempus and Django's ``%I:%M %p`` input format.
    """

    def format_value(self, value):
        if isinstance(value, datetime.datetime):
            h = value.hour
            meridiem = 'PM' if h >= 12 else 'AM'
            h12 = h % 12 or 12
            return (
                f'{value.day:02d}/{value.month:02d}/{value.year} '
                f'{h12:02d}:{value.minute:02d} {meridiem}'
            )
        return super().format_value(value)
