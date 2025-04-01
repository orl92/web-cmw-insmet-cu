import ssl
import smtplib
from django.core.mail.backends.smtp import EmailBackend

class CustomSTARTTLSBackend(EmailBackend):
    def open(self):
        if self.connection:
            return False

        try:
            self.connection = smtplib.SMTP(self.host, self.port)

            # Versión más simple para desactivar verificación
            if self.use_tls:
                self.connection.starttls()
                self.connection.sock.context.verify_mode = ssl.CERT_NONE
                self.connection.sock.context.check_hostname = False

            if self.username and self.password:
                self.connection.login(self.username, self.password)

            return True
        except Exception:
            if not self.fail_silently:
                raise
            return False