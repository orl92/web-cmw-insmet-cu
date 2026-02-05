from django.contrib import messages
from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UserPassesTestMixin,
)
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from common.utils import log_action
from dashboard.forms.servicios.forms import ServiceForm
from dashboard.models import Customer, Service

# Create your views here.


class ServiceListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    template_name = 'pages/dashboard/servicios/listado_servicios.html'
    model = Service
    permission_required = 'dashboard.view_service'
    context_object_name = 'objects'
    
    def dispatch(self, request, *args, **kwargs):
        # Solo permitir acceso a staff, superuser o clientes
        if not (request.user.is_staff or 
                request.user.is_superuser or 
                request.user.groups.filter(name='Clientes').exists()):
            raise PermissionDenied("No tienes permiso para acceder a esta página")
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        """
        Filtra los servicios según el tipo de usuario:
        - Superusuarios y staff: ven todos los servicios
        - Clientes: solo ven servicios comerciales asociados a ellos
        """
        queryset = super().get_queryset()
        
        # Si el usuario es superuser o staff, ve todos los servicios
        if self.request.user.is_superuser or self.request.user.is_staff:
            return queryset.all().order_by('-date')
        
        # Si el usuario pertenece al grupo 'Clientes'
        elif self.request.user.groups.filter(name='Clientes').exists():
            try:
                # Obtener el cliente asociado al usuario
                customer = self.request.user.customer
                # Solo servicios comerciales asociados a este cliente
                return queryset.filter(
                    service_type=Service.COMMERCIAL,
                    target_customer=customer
                ).order_by('-date')
            except Customer.DoesNotExist:
                # Si no tiene perfil de cliente, no ver nada
                return queryset.none()
        
        return queryset.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Listado de Servicios'
        context['parent'] = ''
        context['segment'] = 'servicios'
        context['url_list'] = reverse_lazy('listado_servicios')
        
        # Variables para controlar la visualización en el template
        context['is_client'] = self.request.user.groups.filter(name='clientes').exists()
        context['is_staff'] = self.request.user.is_staff or self.request.user.is_superuser
        context['is_superuser'] = self.request.user.is_superuser
        context['btn'] = 'Añadir Servicio'
        context['url_create'] = reverse_lazy('crear_servicio')
        
        return context


class ServiceCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Service
    form_class = ServiceForm
    template_name = 'pages/dashboard/servicios/crear_servicio.html'
    permission_required = 'dashboard.add_service'
    success_url = reverse_lazy('listado_servicios')
    url_redirect = success_url

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        
        # Registro de acción
        log_action(
            user=self.request.user,
            obj=self.object,
            action_flag=ADDITION,
            message=f"Se creó un nuevo servicio: {self.object.date.strftime('%d-%m-%Y')}."
        )
        
        messages.success(self.request, 'El servicio ha sido creado con éxito.', extra_tags='success')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Añadir Servicio'
        context['parent'] = ''
        context['segment'] = 'servicio'
        context['url_list'] = reverse_lazy('listado_servicios')
        return context


class ServiceUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Service
    form_class = ServiceForm
    template_name = 'pages/dashboard/servicios/actualizar_servicio.html'
    permission_required = 'dashboard.change_service'
    success_url = reverse_lazy('listado_servicios')
    url_redirect = success_url

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(Service, uuid=uuid)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Registro de acción
        log_action(
            user=self.request.user,
            obj=self.object,
            action_flag=CHANGE,
            message=f"Se actualizó el servicio:{self.object.date.strftime('%d-%m-%Y')}."
        )
        
        messages.success(self.request, 'El servicio ha sido actualizado con éxito.', extra_tags='warning')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Actualizar Servicio'
        context['parent'] = ''
        context['segment'] = 'servicio'
        context['url_list'] = reverse_lazy('listado_servicios')
        return context
    
    def test_func(self):
        return self.request.user.is_superuser or self.get_object().user == self.request.user


class ServiceDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Service 
    template_name = 'pages/dashboard/servicios/eliminar_servicio.html'
    permission_required = 'dashboard.delete_service'
    success_url = reverse_lazy('listado_servicios')
    url_redirect = success_url 

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(Service, uuid=uuid) 

    def post(self, request, *args, **kwargs):
        service = self.get_object()
        
        # Registro de acción antes de eliminar
        log_action(
            user=self.request.user,
            obj=service,
            action_flag=DELETION,
            message=f"Se eliminó el servicio: {service.date.strftime('%d-%m-%Y')}."
        )
        
        try:
            service.delete()
            messages.success(request, 'El servicio ha sido eliminado con éxito.', extra_tags='danger')
        except Exception as e:
            messages.error(request, str(e))
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Eliminar Servicio'
        context['parent'] = ''
        context['segment'] = 'servicio'
        context['url_list'] = reverse_lazy('listado_servicios')
        return context
