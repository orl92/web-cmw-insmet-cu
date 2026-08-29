from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.views.generic import ListView

from apps.core.models import ActivityLog


class ActivityLogListView(ListView):
    model = ActivityLog
    template_name = 'pages/core/activity_log.html'
    context_object_name = 'object_list'
    paginate_by = 20

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = ActivityLog.objects.select_related('user', 'content_type').all()

        user_id = self.request.GET.get('user')
        action_flag = self.request.GET.get('action_flag')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')

        if user_id:
            qs = qs.filter(user_id=user_id)
        if action_flag and action_flag.isdigit():
            qs = qs.filter(action_flag=int(action_flag))
        if date_from:
            qs = qs.filter(action_time__date__gte=date_from)
        if date_to:
            qs = qs.filter(action_time__date__lte=date_to)

        return qs.order_by('-action_time')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Auditoría de Actividad'
        context['parent'] = ''
        context['segment'] = 'auditoria'
        context['users'] = (
            User.objects.filter(activity_logs__isnull=False).distinct().order_by('username')
        )
        context['action_flags'] = ActivityLog.ACTIVITY_FLAG_CHOICES
        context['current_filters'] = {
            'user': self.request.GET.get('user', ''),
            'action_flag': self.request.GET.get('action_flag', ''),
            'date_from': self.request.GET.get('date_from', ''),
            'date_to': self.request.GET.get('date_to', ''),
        }
        return context
