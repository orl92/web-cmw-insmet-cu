from datetime import timedelta

from django.contrib import admin
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.core.admin import TaskExecutionLogAdmin
from apps.core.models import SiteConfiguration, TaskExecutionLog


def _disable_maintenance():
    SiteConfiguration.objects.get_or_create(defaults={'maintenance_mode': False})


class TaskMonitoringViewTests(TestCase):
    """Runtime coverage for verify gaps TASK-VIEW-1 and TASK-ADMIN-1."""

    @classmethod
    def setUpTestData(cls):
        _disable_maintenance()
        cls.url = reverse('dashboard:tasks')
        cls.superuser = User.objects.create_superuser(
            'su_monitor',
            'su_monitor@example.com',
            'pass',
            first_name='Su',
            last_name='Monitor',
        )
        # Non-superuser with a complete personal profile and no Customer:
        # the CheckUserProfileMiddleware will NOT redirect, so the view's
        # UserPassesTestMixin (is_superuser) decides access.
        cls.non_superuser = User.objects.create_user(
            'reg_monitor',
            'reg_monitor@example.com',
            'pass',
            first_name='Reg',
            last_name='Monitor',
        )

    def test_non_superuser_blocked(self):
        self.client.force_login(self.non_superuser)
        response = self.client.get(self.url)
        # A complete non-staff profile hits the view guard => 403.
        # (If staff-but-not-superuser, it would redirect to login => 302.)
        self.assertIn(response.status_code, (403, 302))
        self.assertEqual(response.status_code, 403)

    def test_superuser_allowed(self):
        self.client.force_login(self.superuser)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_stale_queue_banner(self):
        now = timezone.now()
        TaskExecutionLog.objects.create(
            task_id='stale-1',
            task_name='send_email_task',
            status=TaskExecutionLog.STATUS_ENQUEUED,
            enqueued_at=now - timedelta(minutes=10),
        )
        self.client.force_login(self.superuser)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn('en cola sin iniciar por más de', content)
        self.assertIn('alert-danger', content)
        self.assertIn('<strong>1</strong>', content)

    def test_badge_uses_lt_style(self):
        """La tabla usa badges con estilo Tabler bg-*-lt (convención del proyecto)."""
        TaskExecutionLog.objects.create(
            task_id='err-badge-1',
            task_name='send_email_task',
            status=TaskExecutionLog.STATUS_ERROR,
            enqueued_at=timezone.now(),
        )
        TaskExecutionLog.objects.create(
            task_id='enqueued-badge-1',
            task_name='send_email_task',
            status=TaskExecutionLog.STATUS_ENQUEUED,
            enqueued_at=timezone.now(),
        )
        self.client.force_login(self.superuser)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn('badge bg-danger-lt', content)
        self.assertIn('badge bg-info-lt', content)

    def test_actions_use_icons_and_tooltips(self):
        """ "Acciones con iconos + tooltips y args truncadas (estilo listados)."""
        long_args = 'arg1=' + 'x' * 200
        TaskExecutionLog.objects.create(
            task_id='err-icon-1',
            task_name='generate_invoice_pdf_and_email_task',
            status=TaskExecutionLog.STATUS_ERROR,
            enqueued_at=timezone.now(),
            func_name='apps.core.tasks.generate_invoice_pdf_and_email_task',
            func_args='{}',
            args_repr=long_args,
        )
        self.client.force_login(self.superuser)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        # Botones de acción con clase btn-icon y tooltip.
        self.assertIn('btn-icon btn-outline-danger btn-sm', content)
        self.assertIn('data-bs-toggle="tooltip"', content)
        # Iconos de las acciones (traceback / reintentar / eliminar).
        self.assertIn('ti-code', content)
        self.assertIn('ti-refresh', content)
        self.assertIn('ti-trash', content)
        # Args truncadas: el texto NO muestra los 200 chars pero el title sí.
        self.assertNotIn(long_args + '</td>', content)
        self.assertIn('title="' + long_args.replace('"', '&quot;') + '"', content)

    def test_delete_uses_confirm_modal(self):
        """ "Eliminar" abre el modal de confirmación (estilo listados)."""
        TaskExecutionLog.objects.create(
            task_id='del-modal-1',
            task_name='send_email_task',
            status=TaskExecutionLog.STATUS_ERROR,
            enqueued_at=timezone.now(),
        )
        self.client.force_login(self.superuser)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        # Botón con data-action->eliminar + pk + tooltip "Eliminar".
        self.assertIn('action-btn', content)
        self.assertIn('data-action="eliminar"', content)
        self.assertIn('data-bs-original-title="Eliminar">', content)
        # El modal de confirmación está presente con su form.
        self.assertIn('id="confirmTaskDeleteModal"', content)
        self.assertIn('id="confirmTaskDeleteForm"', content)
        self.assertIn('name="action" value="delete"', content)


class TaskMonitoringActionTests(TestCase):
    """Acciones POST sobre un registro de tarea: reintentar y eliminar."""

    @classmethod
    def setUpTestData(cls):
        _disable_maintenance()
        cls.url = reverse('dashboard:tasks')
        cls.superuser = User.objects.create_superuser(
            'su_mon_action',
            'su_mon_action@example.com',
            'pass',
            first_name='Su',
            last_name='Action',
        )
        # El middleware CheckUserProfileMiddleware exige email + nombres completos.
        cls.non_superuser = User.objects.create_user(
            'reg_mon_action',
            'reg_mon_action@example.com',
            'pass',
            first_name='Reg',
            last_name='Action',
        )

    @staticmethod
    def _log(**overrides):
        defaults = {
            'task_id': 'task-action-1',
            'task_name': 'generate_invoice_pdf_and_email_task',
            'status': TaskExecutionLog.STATUS_ERROR,
            'enqueued_at': timezone.now(),
            'func_name': 'apps.core.tasks.generate_invoice_pdf_and_email_task',
            'func_args': '{"args": ["00000000-0000-0000-0000-000000000000", "http://x"]}',
        }
        defaults.update(overrides)
        return TaskExecutionLog.objects.create(**defaults)

    def test_retry_reenqueues_task(self):
        execution = self._log()
        from config.huey import huey

        pending_before = huey.pending_count()
        self.client.force_login(self.superuser)
        response = self.client.post(
            reverse('dashboard:tasks_action', args=[execution.pk]),
            {'action': 'retry'},
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.url)
        # La tarea fue reencolada en la cola persistente.
        self.assertEqual(huey.pending_count(), pending_before + 1)

    def test_retry_non_retryable_rejected(self):
        execution = self._log(
            task_name='send_email_task',
            func_name='apps.core.tasks.send_email_task',
            func_args='',
        )
        self.client.force_login(self.superuser)
        response = self.client.post(
            reverse('dashboard:tasks_action', args=[execution.pk]),
            {'action': 'retry'},
        )
        self.assertEqual(response.status_code, 302)
        # El registro sigue igual: no se reencoló ni se modificó.
        execution.refresh_from_db()
        self.assertEqual(execution.status, TaskExecutionLog.STATUS_ERROR)

    def test_delete_removes_log(self):
        execution = self._log()
        self.client.force_login(self.superuser)
        response = self.client.post(
            reverse('dashboard:tasks_action', args=[execution.pk]),
            {'action': 'delete'},
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(TaskExecutionLog.objects.filter(pk=execution.pk).exists())

    def test_non_superuser_blocked_from_action(self):
        execution = self._log()
        self.client.force_login(
            User.objects.create_user(
                'reg_mon_action2',
                'reg_mon_action2@example.com',
                'pass',
                first_name='Reg',
                last_name='Action',
            )
        )
        response = self.client.post(
            reverse('dashboard:tasks_action', args=[execution.pk]),
            {'action': 'delete'},
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue(TaskExecutionLog.objects.filter(pk=execution.pk).exists())


class TaskExecutionLogAdminTests(TestCase):
    """Runtime coverage for verify gap TASK-ADMIN-1 (admin status filter)."""

    @classmethod
    def setUpTestData(cls):
        cls.superuser = User.objects.create_superuser(
            'su_admin_mon',
            'su_admin_mon@example.com',
            'pass',
            first_name='Su',
            last_name='Admin',
        )

    def test_registered_and_readonly(self):
        self.assertIn(TaskExecutionLog, admin.site._registry)
        admin_class = admin.site._registry[TaskExecutionLog]
        self.assertIsInstance(admin_class, TaskExecutionLogAdmin)
        self.assertFalse(admin_class.has_add_permission(None))
        self.assertFalse(admin_class.has_change_permission(None))
        self.assertIn('status', admin_class.list_filter)

    def test_status_filter_returns_only_matching(self):
        now = timezone.now()
        TaskExecutionLog.objects.create(
            task_id='err-1',
            task_name='send_email_task',
            status=TaskExecutionLog.STATUS_ERROR,
            enqueued_at=now,
        )
        TaskExecutionLog.objects.create(
            task_id='ok-1',
            task_name='send_email_task',
            status=TaskExecutionLog.STATUS_SUCCESS,
            enqueued_at=now,
        )
        rf = RequestFactory()
        request = rf.get('/admin/core/taskexecutionlog/?status__exact=ERROR')
        request.user = self.superuser
        changelist = TaskExecutionLogAdmin(TaskExecutionLog, admin.site).get_changelist_instance(
            request
        )
        qs = changelist.get_queryset(request)
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().status, TaskExecutionLog.STATUS_ERROR)
