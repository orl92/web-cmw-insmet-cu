from django.contrib import messages
from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UserPassesTestMixin,
)
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView, View

from apps.commercial.forms.service import ServiceForm
from apps.commercial.models import Service
from apps.core.utils import log_action
from apps.core.views import ServeModelFileView


class ServiceListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    template_name = 'pages/commercial/service/list.html'
    model = Service
    permission_required = 'commercial.view_service'
    context_object_name = 'objects'

    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_staff or request.user.is_superuser):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return (
            Service.objects.select_related('user')
            .annotate(num_subscriptions=Count('servicesubscription'))
            .order_by('-date')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Listado de Servicios'
        context['parent'] = ''
        context['segment'] = 'servicios'
        context['btn'] = 'Añadir Servicio'
        context['url_create'] = reverse_lazy('commercial:servicio_create')
        context['url_list'] = reverse_lazy('commercial:servicio_list')
        context['is_superuser'] = self.request.user.is_superuser
        return context


class ServiceCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Service
    form_class = ServiceForm
    template_name = 'pages/commercial/service/create.html'
    permission_required = 'commercial.add_service'
    success_url = reverse_lazy('commercial:servicio_list')
    url_redirect = success_url

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        log_action(
            user=self.request.user,
            obj=self.object,
            action_flag=ADDITION,
            message=f'Se creó el servicio: {self.object.title}',
        )
        messages.success(self.request, 'Servicio creado con éxito.')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Añadir Servicio'
        context['parent'] = ''
        context['segment'] = 'servicio'
        context['url_list'] = reverse_lazy('commercial:servicio_list')
        return context


class ServiceUpdateView(
    LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin, UpdateView
):
    model = Service
    form_class = ServiceForm
    template_name = 'pages/commercial/service/update.html'
    permission_required = 'commercial.change_service'
    success_url = reverse_lazy('commercial:servicio_list')
    url_redirect = success_url

    def get_object(self, queryset=None):
        return get_object_or_404(Service, uuid=self.kwargs['uuid'])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def test_func(self):
        return self.request.user.is_superuser or self.get_object().user == self.request.user

    def post(self, request, *args, **kwargs):
        # El tipo de servicio es inmutable al editar: se fuerza al valor del
        # objeto aunque el cliente envíe otro valor (el select está disabled).
        self.object = self.get_object()
        post = request.POST.copy()
        post['service_type'] = self.object.service_type
        request.POST = post
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save()
        log_action(
            user=self.request.user,
            obj=self.object,
            action_flag=CHANGE,
            message=f'Se actualizó el servicio: {self.object.title}',
        )
        messages.success(self.request, 'Servicio actualizado con éxito.')
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Actualizar Servicio'
        context['parent'] = ''
        context['segment'] = 'servicio'
        context['url_list'] = reverse_lazy('commercial:servicio_list')
        return context


class ServiceDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Soft delete: desactiva el servicio."""

    permission_required = 'commercial.delete_service'

    def post(self, request, uuid):
        service = get_object_or_404(Service, uuid=uuid)
        if not service.record_active:
            messages.warning(request, 'El servicio ya estaba desactivado.')
            return redirect('commercial:servicio_list')
        service.delete()
        log_action(
            user=self.request.user,
            obj=service,
            action_flag=DELETION,
            message=f'Servicio desactivado: {service.title}.',
        )
        messages.success(request, 'Servicio desactivado con éxito.')
        return redirect('commercial:servicio_list')


class ServiceReactivateView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Reactivación: vuelve a activar un servicio desactivado (soft delete inverso)."""

    permission_required = 'commercial.change_service'

    def post(self, request, uuid):
        service = get_object_or_404(Service, uuid=uuid)
        if service.record_active:
            messages.warning(request, 'El servicio ya estaba activo.')
            return redirect('commercial:servicio_list')
        service.record_active = True
        service.deleted_at = None
        service.save(update_fields=['record_active', 'deleted_at'])
        log_action(
            user=self.request.user,
            obj=service,
            action_flag=CHANGE,
            message=f'Servicio reactivado: {service.title}.',
        )
        messages.success(request, 'Servicio reactivado con éxito.')
        return redirect('commercial:servicio_list')


class ServiceHardDeleteView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Eliminación física permanente (solo superusuarios)."""

    def test_func(self):
        return self.request.user.is_superuser

    def post(self, request, uuid):
        service = get_object_or_404(Service, uuid=uuid)
        service_title = service.title
        service.hard_delete()
        log_action(
            user=self.request.user,
            obj=service,
            action_flag=DELETION,
            message=f'Servicio eliminado físicamente: {service_title}.',
        )
        messages.success(request, f'Servicio {service_title} eliminado permanentemente.')
        return redirect('commercial:servicio_list')


class ServicePDFDownloadView(ServeModelFileView):
    model = Service
    field = 'pdf'
    permission_required = 'commercial.view_service'

    def get_filename(self, obj):
        return f'servicio_{obj.uuid}.pdf'
