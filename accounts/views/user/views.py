from django.contrib import messages
from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from django.contrib.auth import login
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UserPassesTestMixin)
from django.contrib.auth.models import Group, User
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView, View

from accounts.forms.user.form import CustomerSignUpForm, UserForm, UserUpdateForm
from accounts.models import Profile
from common.utils import log_action
from dashboard.models import Customer

# Create your views here.


class UserListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = User
    template_name = 'pages/accounts/users/users.html'
    permission_required = 'auth.view_user'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Listado de Usuarios'
        context['parent'] = 'accounts'
        context['segment'] = 'users'
        context['btn'] = 'Añadir Usuario'
        context['url_create'] = reverse_lazy('create_user')
        context['url_list'] = reverse_lazy('users')
        context['is_staff'] = self.request.user.is_staff or self.request.user.is_superuser
        context['is_superuser'] = self.request.user.is_superuser
        context["objects"] = User.objects.all()
        return context


class UserCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = User
    form_class = UserForm
    template_name = 'pages/accounts/users/user_create.html'
    permission_required = 'auth.add_user'  # Permiso requerido para añadir un usuario
    success_url = reverse_lazy('users')
    url_redirect = success_url

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_active = True
        user.save()
        profile, created = Profile.objects.get_or_create(user=user)
        profile.save()
        
        # Registro de acción
        log_action(
            user=self.request.user,
            obj=user,
            action_flag=ADDITION,
            message=f"Se creó un nuevo usuario {user.username}."
        )
        
        messages.success(self.request, 'El usuario ha sido creado con éxito.', extra_tags='success')
        return redirect('update_user', uuid=profile.uuid)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Añadir Usuarios'
        context['parent'] = 'accounts'
        context['segment'] = 'users'
        context['url_list'] = self.success_url
        return context


class UserUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin, UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = 'pages/accounts/users/user_update.html'
    permission_required = 'auth.change_user'
    success_url = reverse_lazy('users')
    url_redirect = success_url

    def get_object(self):
        uuid = self.kwargs.get('uuid')
        profile = get_object_or_404(Profile, uuid=uuid)
        return profile.user

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = self.get_object()
        return kwargs

    def form_valid(self, form):
        user = self.get_object()
        old_group_names = {g.name for g in user.groups.all()}
        new_group_names = {g.name for g in form.cleaned_data.get('groups', [])}

        if 'Clientes' in old_group_names and 'Clientes' not in new_group_names and hasattr(user, 'customer'):
            form.add_error(
                'groups',
                'No puede quitar el grupo "Clientes" a un usuario que tiene perfil de cliente. '
                'Desactive el cliente desde el listado de clientes si es necesario.'
            )
            return self.form_invalid(form)

        response = super().form_valid(form)
        user = self.object

        if 'Clientes' not in old_group_names and 'Clientes' in new_group_names and not hasattr(user, 'customer'):
            log_action(
                user=self.request.user,
                obj=user,
                action_flag=CHANGE,
                message=f"Se asignó el grupo Clientes a {user.username}. Redirigiendo a completar datos."
            )
            messages.info(
                self.request,
                'Complete los datos del cliente para este usuario.',
                extra_tags='info'
            )
            return redirect('crear_cliente_para_usuario', user_uuid=user.profile.uuid)

        log_action(
            user=self.request.user,
            obj=self.object,
            action_flag=CHANGE,
            message=f"Se editó el perfil de {self.object.username}."
        )

        messages.success(self.request, 'El usuario ha sido actualizado con éxito.', extra_tags='warning')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Actualizar Usuario'
        context['parent'] = 'accounts'
        context['segment'] = 'users'
        context['url_list'] = self.success_url
        return context

    def test_func(self):
        user = self.get_object()
        return self.request.user.is_superuser or user == self.request.user


class UserDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'auth.delete_user'

    def post(self, request, uuid):
        profile = get_object_or_404(Profile, uuid=uuid)
        user = profile.user
        if user.is_superuser and User.objects.filter(is_superuser=True).count() == 1:
            messages.error(request, f'No se puede eliminar el usuario {user.username} si es el único superusuario.')
            return redirect('users')
        log_action(
            user=self.request.user,
            obj=user,
            action_flag=DELETION,
            message=f"Se eliminó al usuario {user.username}."
        )
        user.delete()
        messages.success(request, f'Usuario {user.username} se ha eliminado correctamente.')
        return redirect('users')

class CustomerRegisterView(CreateView):
    form_class = CustomerSignUpForm
    template_name = 'pages/accounts/users/customer_register.html'
    success_url = reverse_lazy('public_servicios_comerciales')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, 'Ya tienes una sesión activa.')
            return redirect('public_servicios_comerciales')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        try:
            user = form.save()
        except IntegrityError:
            messages.error(
                self.request,
                'El código REEUP o NIT ya existe. Por favor, verifique los datos.'
            )
            return redirect(self.request.path)

        login(self.request, user)

        try:
            customer = Customer.objects.get(user=user)
            log_action(
                user=user,
                obj=customer,
                action_flag=ADDITION,
                message=f"Cliente registrado desde formulario público: {customer.company_name}."
            )
        except Customer.DoesNotExist:
            pass

        messages.success(
            self.request,
            f'¡Registro exitoso! Bienvenido/a {form.cleaned_data["company_name"]}. '
            'Ahora puedes acceder a tus servicios comerciales.',
            extra_tags='success'
        )
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Registro Empresas'
        context['parent'] = ''
        context['segment'] = 'registro'
        context['is_registration'] = True
        return context
