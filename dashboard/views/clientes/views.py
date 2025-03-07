from django.contrib import messages
from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin,
                                        UserPassesTestMixin)
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from dashboard.forms.clientes.forms import CustomerForm, CustomerUpdateForm
from dashboard.models import Customer

from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from common.utils import log_action


class CustomerListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    template_name = 'pages/dashboard/clientes/listado_clientes.html'
    model = Customer
    permission_required = 'dashboard.view_customer'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Clientes'
        context['parent'] = ''
        context['segment'] = 'clientes'
        context['btn'] = 'Añadir Cliente'
        context['url_create'] = reverse_lazy('crear_cliente')
        context['url_list'] = reverse_lazy('listado_clientes')
        context['objects'] = Customer.objects.all()
        return context

class CustomerCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'pages/dashboard/clientes/crear_cliente.html'
    permission_required = 'dashboard.add_customer'
    success_url = reverse_lazy('listado_clientes')

    def form_valid(self, form):
        response = super().form_valid(form)
        customer = self.object
        
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
        context['url_list'] = reverse_lazy('listado_clientes')
        return context

class CustomerUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Customer
    form_class = CustomerUpdateForm
    template_name = 'pages/dashboard/clientes/actualizar_cliente.html'
    permission_required = 'dashboard.change_customer'
    success_url = reverse_lazy('listado_clientes')

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
        context['url_list'] = reverse_lazy('listado_clientes')
        return context  

    def test_func(self):
        return self.request.user.is_superuser or self.get_object().user == self.request.user 

class CustomerDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Customer
    template_name = 'pages/dashboard/clientes/eliminar_cliente.html'
    permission_required = 'dashboard.delete_customer'
    success_url = reverse_lazy('listado_clientes')
    url_redirect = success_url

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(Customer, uuid=uuid)

    def delete(self, request, *args, **kwargs):
        customer = self.get_object()
        user = customer.user

        # Registro de acción antes de eliminar
        log_action(
            user=self.request.user,
            obj=customer,
            action_flag=DELETION,
            message=f"Se eliminó el cliente y el usuario asociado: {customer.user.username}."
        )
        
        try:
            response = super().delete(request, *args, **kwargs)
            user.delete()  # Eliminar el usuario asociado
            messages.success(self.request, 'El cliente y el usuario asociado han sido eliminados con éxito.', extra_tags='danger')
            return response
        except Customer.DoesNotExist:
            messages.error(self.request, 'El cliente no existe o ya ha sido eliminado.', extra_tags='danger')
            return redirect(self.success_url)
        except Exception as e:
            messages.error(self.request, f'Error al eliminar el cliente: {str(e)}', extra_tags='danger')
            return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Eliminar Cliente'
        context['parent'] = ''
        context['segment'] = 'cliente'
        context['url_list'] = reverse_lazy('listado_clientes')
        return context
