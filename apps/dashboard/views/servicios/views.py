from django.contrib import messages
from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UserPassesTestMixin)
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView, View

from apps.common.utils import log_action
from apps.dashboard.forms.servicios.forms import ServiceForm
from apps.crm.models import Service


class ServiceListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    template_name = 'pages/dashboard/servicios/listado_servicios.html'
    model = Service
    permission_required = 'dashboard.view_service'
    paginate_by = 20
    context_object_name = 'objects'

    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_staff or request.user.is_superuser):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return Service.objects.select_related('user').annotate(
            num_subscriptions=Count('servicesubscription')
        ).order_by('-date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Listado de Servicios'
        context['parent'] = ''
        context['segment'] = 'servicios'
        context['btn'] = 'Añadir Servicio'
        context['url_create'] = reverse_lazy('dashboard:servicio_create')
        context['url_list'] = reverse_lazy('dashboard:servicio_list')
        context['url_export'] = reverse_lazy('dashboard:servicio_export_csv')
        context['is_superuser'] = self.request.user.is_superuser
        return context


class ServiceCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Service
    form_class = ServiceForm
    template_name = 'pages/dashboard/servicios/crear_servicio.html'
    permission_required = 'dashboard.add_service'
    success_url = reverse_lazy('dashboard:servicio_list')
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
            message=f"Se creó el servicio: {self.object.title}"
        )
        messages.success(self.request, 'Servicio creado con éxito.')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Añadir Servicio'
        context['parent'] = ''
        context['segment'] = 'servicio'
        context['url_list'] = reverse_lazy('dashboard:servicio_list')
        return context


class ServiceUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Service
    form_class = ServiceForm
    template_name = 'pages/dashboard/servicios/actualizar_servicio.html'
    permission_required = 'dashboard.change_service'
    success_url = reverse_lazy('dashboard:servicio_list')
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
        self.object = self.get_object()
        old_type = self.object.service_type
        new_type = request.POST.get('service_type')

        # Si cambia el tipo, eliminar el archivo que ya no corresponde (en memoria)
        if old_type != new_type:
            if new_type == Service.PUBLIC:
                self.object.image = None   # Eliminar imagen si existe
            elif new_type == Service.COMMERCIAL:
                self.object.pdf = None     # Eliminar PDF si existe

        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        self.object = form.save()
        log_action(
            user=self.request.user,
            obj=self.object,
            action_flag=CHANGE,
            message=f"Se actualizó el servicio: {self.object.title}"
        )
        messages.success(self.request, 'Servicio actualizado con éxito.')
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Actualizar Servicio'
        context['parent'] = ''
        context['segment'] = 'servicio'
        context['url_list'] = reverse_lazy('dashboard:servicio_list')
        return context


class ServiceDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Soft delete: desactiva el servicio."""
    permission_required = 'dashboard.delete_service'

    def post(self, request, uuid):
        service = get_object_or_404(Service, uuid=uuid)
        if not service.record_active:
            messages.warning(request, 'El servicio ya estaba desactivado.')
            return redirect('dashboard:servicio_list')
        service.delete()
        log_action(
            user=self.request.user,
            obj=service,
            action_flag=DELETION,
            message=f"Servicio desactivado: {service.title}."
        )
        messages.success(request, 'Servicio desactivado con éxito.')
        return redirect('dashboard:servicio_list')


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
            message=f"Servicio eliminado físicamente: {service_title}."
        )
        messages.success(request, f'Servicio {service_title} eliminado permanentemente.')
        return redirect('dashboard:servicio_list')
