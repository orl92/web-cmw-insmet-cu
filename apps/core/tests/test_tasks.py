import datetime
import os
import tempfile

from django.core import mail
from django.test import SimpleTestCase, TestCase, override_settings

from apps.core.tasks import send_email_task
from config.huey import huey

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


class RetryBackoffTests(SimpleTestCase):
    """La espera entre reintentos tiene que CRECER de verdad.

    Estuvo en `retry_backoff=True` y eso no hacia nada: huey multiplica la espera
    por ese valor en cada reintento (`task.retry_delay *= task.retry_backoff`), y
    `True` es truthy pero vale 1, asi que las tres esperas eran de 30 s. El sintoma
    era invisible en los tests: nadie mireaba la espera, solo el exito.
    """

    tareas = (
        'apps.core.tasks.generate_invoice_pdf_and_email_task',
        'apps.core.tasks.send_email_task',
    )

    def test_el_backoff_es_un_numero_y_no_un_booleano(self):
        for nombre in self.tareas:
            with self.subTest(tarea=nombre):
                task = self._task(nombre)
                self.assertNotIsInstance(
                    task.retry_backoff,
                    bool,
                    f'{nombre}: True es truthy pero vale 1, el backoff no crece',
                )
                self.assertGreater(task.retry_backoff, 1)

    def test_la_espera_crece_en_cada_reintento(self):
        for nombre in self.tareas:
            with self.subTest(tarea=nombre):
                task = self._task(nombre)
                ahora = datetime.datetime.now()
                esperas = [task.retry_delay]
                for _ in range(task.retries):
                    huey._requeue_task(task, ahora)
                    esperas.append(task.retry_delay)

                self.assertEqual(len(set(esperas)), len(esperas), f'{nombre}: la espera se repitio')
                self.assertEqual(esperas, sorted(esperas), f'{nombre}: la espera no crece')
                self.assertTrue(
                    all(b > a for a, b in zip(esperas, esperas[1:], strict=False)),
                    f'{nombre}: esperas {esperas} sin crecimiento real',
                )

    def test_el_eta_se_aleja_en_cada_reintento(self):
        task = self._task('apps.core.tasks.send_email_task')
        ahora = datetime.datetime.now()
        etas = []
        for _ in range(task.retries):
            huey._requeue_task(task, ahora)
            etas.append(task.eta)

        self.assertEqual(len(set(etas)), len(etas), f'etas repetidos: {etas}')

    @staticmethod
    def _task(nombre):
        """La clase `Task` que huey registro para esa tarea, ya instanciada."""
        return huey._registry._registry[nombre]()
