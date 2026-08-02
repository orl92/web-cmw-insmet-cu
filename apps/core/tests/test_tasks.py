import os
import tempfile

from django.core import mail
from django.test import TestCase, override_settings

from apps.core.tasks import send_email_task

LOCMEM = 'django.core.mail.backends.locmem.EmailBackend'


@override_settings(EMAIL_BACKEND=LOCMEM)
class SendEmailTaskTests(TestCase):
    def setUp(self):
        mail.outbox = []

    def test_sends_html_email(self):
        send_email_task.call_local(
            subject='Asunto',
            html_message='<p>Hola</p>',
            from_email='from@example.com',
            recipients=['to@example.com'],
        )
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertEqual(msg.subject, 'Asunto')
        self.assertEqual(msg.content_subtype, 'html')
        self.assertEqual(msg.to, ['to@example.com'])

    def test_sends_with_attachment_args(self):
        send_email_task.call_local(
            subject='Con adjunto',
            html_message='<p>PDF</p>',
            from_email='from@example.com',
            recipients=['to@example.com'],
            attachment_name='doc.pdf',
            attachment_content=b'%PDF-1.4 data',
            attachment_mime='application/pdf',
        )
        msg = mail.outbox[0]
        self.assertEqual(len(msg.attachments), 1)
        name, content, mime = msg.attachments[0]
        self.assertEqual(name, 'doc.pdf')
        self.assertEqual(content, b'%PDF-1.4 data')
        self.assertEqual(mime, 'application/pdf')

    def test_sends_with_attachment_path(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as f:
            f.write(b'%PDF-1.4 from path')
            path = f.name
        try:
            send_email_task.call_local(
                subject='Por path',
                html_message='<p>PDF</p>',
                from_email='from@example.com',
                recipients=['to@example.com'],
                attachment_path=path,
            )
            msg = mail.outbox[0]
            self.assertEqual(len(msg.attachments), 1)
            name, content, mime = msg.attachments[0]
            self.assertEqual(name, os.path.basename(path))
            self.assertEqual(content, b'%PDF-1.4 from path')
            self.assertEqual(mime, 'application/pdf')
        finally:
            os.remove(path)

    def test_no_attachments_by_default(self):
        send_email_task.call_local(
            subject='Sin adjunto',
            html_message='<p>Hola</p>',
            from_email='from@example.com',
            recipients=['to@example.com'],
        )
        self.assertEqual(mail.outbox[0].attachments, [])

    def test_missing_attachment_path_is_ignored(self):
        send_email_task.call_local(
            subject='Path inexistente',
            html_message='<p>Hola</p>',
            from_email='from@example.com',
            recipients=['to@example.com'],
            attachment_path='/no/existe/archivo.pdf',
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].attachments, [])
