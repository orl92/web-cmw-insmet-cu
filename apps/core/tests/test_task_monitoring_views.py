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
