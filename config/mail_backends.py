"""Backends de correo para DESARROLLO local. NO usar en producción.

El Poste.io local (Docker) sirve SMTP con un certificado autofirmado sin
CN ni subjectAltName (subject = ``O=Poste.io``). La verificación estándar
de OpenSSL no puede validarlo por más que se confíe la CA, porque no hay
ningún nombre contra el cual verificar el host.

Este backend reutiliza ``django.core.mail.backends.smtp.EmailBackend`` y
solo cambia el contexto TLS: desactiva verificación de host y de cadena.
TODO lo demás (auth SMTP, STARTTLS, adjuntos, cola) es idéntico al backend
estándar. Se activa desde ``.env``:

    EMAIL_BACKEND=config.mail_backends.InsecureDevEmailBackend

Nunca apuntar esta clase en producción (``requirements/prod.txt`` + systemd):
ahí el SMTP real debe verificarse con el backend estándar. El perfil de
producción lo rechaza explícitamente (``config/settings/production.py``, con la
lista ``insecure_email_backends`` de ``config/settings/base.py``): el envío
"funciona" y nadie se entera de que el mensaje viaja sin cifrar.
"""

import ssl

from django.core.mail.backends.smtp import EmailBackend
from django.utils.functional import cached_property


class InsecureDevEmailBackend(EmailBackend):
    """SMTP con TLS sin verificación de certificado (solo desarrollo)."""

    @cached_property
    def ssl_context(self):
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        return context
