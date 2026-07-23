from django.contrib import messages
from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UserPassesTestMixin)
from django.contrib.auth.models import Group, User
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView, View

from apps.accounts.models import Profile
from apps.common.utils import log_action
from apps.dashboard.forms.clientes.forms import (
    CustomerForUserForm,
    CustomerForm,
    CustomerUpdateForm)
from apps.dashboard.models import Customer


class CustomerListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    template_name = 'pages/dashboard/clientes/listado_clientes.html'
    model = Customer
    permission_required = 'dashboard.view_customer'
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Clientes'
        context['parent'] = ''
        context['segment'] = 'clientes'
        context['btn'] = 'Añadir Cliente'
        context['url_create'] = reverse_lazy('dashboard:cliente_create')
        context['url_list'] = reverse_lazy('dashboard:cliente_list')
        context['url_export'] = reverse_lazy('dashboard:cliente_export_csv')
        context['is_superuser'] = self.request.user.is_superuser
        context['objects'] = Customer.objects.all().select_related('user')
        return context


class CustomerCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'pages/dashboard/clientes/crear_cliente.html'
    permission_required = 'dashboard.add_customer'
    success_url = reverse_lazy('dashboard:cliente_list')
    url_redirect = success_url

    def form_valid(self, form):
        response = super().form_valid(form)
        customer = self.object
        
        # Asignar al grupo "clientes"
        try:
            clientes_group = Group.objects.get(name='Clientes')
            customer.user.groups.add(clientes_group)
        except Group.DoesNotExist:
            # Si no existe, crear el grupo
            clientes_group = Group.objects.create(name='Clientes')
            customer.user.groups.add(clientes_group)
        
        # Registro de acción
        log_action(
            user=self.request.user,
            obj=customer,
            action_flag=ADDITION,
            message=f"Se creó un nuevo cliente: {customer.user.username}."
        )

        messages.success(self.request, f'Cliente creado con éxito. Nombre de usuario: {customer.user.username}', extra_tags='success')
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Añadir Cliente'
        context['parent'] = ''
        context['segment'] = 'cliente'
        context['url_list'] = self.success_url
        return context 


class CustomerUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Customer
    form_class = CustomerUpdateForm
    template_name = 'pages/dashboard/clientes/actualizar_cliente.html'
    permission_required = 'dashboard.change_customer'
    success_url = reverse_lazy('dashboard:cliente_list')
    url_redirect = success_url

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(Customer, uuid=uuid)

    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Registro de acción
        log_action(
            user=self.request.user,
            obj=self.object,
            action_flag=CHANGE,
            message=f"Se actualizó el cliente: {self.object.user.username}."
        )

        messages.success(self.request, 'El cliente ha sido actualizado con éxito.', extra_tags='warning')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Actualizar Cliente'
        context['parent'] = ''
        context['segment'] = 'cliente'
        context['url_list'] = self.success_url
        return context  

    def test_func(self):
        return self.request.user.is_superuser or self.get_object().user == self.request.user 


class CustomerDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Soft delete: desactiva el cliente sin borrar su usuario."""
    permission_required = 'dashboard.delete_customer'

    def post(self, request, uuid):
        customer = get_object_or_404(Customer, uuid=uuid)
        if not customer.record_active:
            messages.warning(request, 'El cliente ya estaba desactivado.')
            return redirect('dashboard:cliente_list')
        customer.delete()
        log_action(
            user=self.request.user,
            obj=customer,
            action_flag=DELETION,
            message=f"Cliente desactivado: {customer.company_name}."
        )
        messages.success(request, 'Cliente desactivado con éxito.')
        return redirect('dashboard:cliente_list')


class CustomerHardDeleteView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Eliminación física permanente (solo superusuarios)."""
    def test_func(self):
        return self.request.user.is_superuser

    def post(self, request, uuid):
        customer = get_object_or_404(Customer, uuid=uuid)
        company_name = customer.company_name
        user = customer.user
        customer.hard_delete()
        try:
            user.delete()
        except Exception:
            pass
        log_action(
            user=self.request.user,
            obj=customer,
            action_flag=DELETION,
            message=f"Cliente eliminado físicamente: {company_name}."
        )
        messages.success(request, f'Cliente {company_name} eliminado permanentemente.')
        return redirect('dashboard:cliente_list')


class CustomerCreateForUserView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Customer
    form_class = CustomerForUserForm
    template_name = 'pages/dashboard/clientes/crear_cliente_para_usuario.html'
    permission_required = 'dashboard.add_customer'
    success_url = reverse_lazy('dashboard:cliente_list')
    url_redirect = success_url

    def dispatch(self, request, *args, **kwargs):
        uuid = self.kwargs.get('user_uuid')
        self.user = get_object_or_404(Profile, uuid=uuid).user
        if hasattr(self.user, 'customer'):
            messages.warning(request, 'Este usuario ya tiene un perfil de cliente.')
            return redirect('dashboard:cliente_list')
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.user
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        customer = self.object

        try:
            clientes_group = Group.objects.get(name='Clientes')
            customer.user.groups.add(clientes_group)
        except Group.DoesNotExist:
            clientes_group = Group.objects.create(name='Clientes')
            customer.user.groups.add(clientes_group)

        log_action(
            user=self.request.user,
            obj=customer,
            action_flag=ADDITION,
            message=f"Cliente creado desde usuario existente: {customer.user.username}."
        )

        messages.success(
            self.request,
            f'Datos de cliente completados para {customer.user.username}.',
            extra_tags='success'
        )
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Completar Datos del Cliente'
        context['parent'] = ''
        context['segment'] = 'clientes'
        context['url_list'] = self.success_url
        context['customer_user'] = self.user
        return context
