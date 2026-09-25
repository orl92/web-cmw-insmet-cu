from django.contrib import messages
from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from django.contrib.auth import login
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UserPassesTestMixin,
)
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView, View

from apps.commercial.models import Customer
from apps.core.utils import log_action
from apps.user_auth.forms.users import CustomerSignUpForm, UserForm, UserUpdateForm
from apps.user_auth.models import Profile

CLIENTES_GROUP_NAME = 'Clientes'


class UserListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = User
    template_name = 'pages/user_auth/users/list.html'
    permission_required = 'auth.view_user'

    def get_queryset(self):
        return User.objects.select_related('profile').prefetch_related('groups')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Listado de Usuarios'
        context['parent'] = 'user_auth'
        context['segment'] = 'users'
        context['btn'] = 'Añadir Usuario'
        context['url_create'] = reverse_lazy('user_auth:user_create')
        context['url_list'] = reverse_lazy('user_auth:users_list')
        context['is_superuser'] = self.request.user.is_superuser
        context['objects'] = self.object_list
        return context


class UserCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = User
    form_class = UserForm
    template_name = 'pages/user_auth/users/create.html'
    permission_required = 'auth.add_user'
    success_url = reverse_lazy('user_auth:users_list')
    url_redirect = success_url

    def form_valid(self, form):
        with transaction.atomic():
            user = form.save(commit=False)
            user.is_active = True
            user.save()
            # El Profile lo crea la señal post_save del modelo User
            # (apps/user_auth/models.py); aquí solo se lee.
            profile = user.profile

            log_action(
                user=self.request.user,
                obj=user,
                action_flag=ADDITION,
                message=f'Se creó un nuevo usuario {user.username}.',
                request=self.request,
            )

        messages.success(self.request, 'El usuario ha sido creado con éxito.', extra_tags='success')
        return redirect('user_auth:user_update', uuid=profile.uuid)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Añadir Usuarios'
        context['parent'] = 'user_auth'
        context['segment'] = 'users'
        context['url_list'] = self.success_url
        return context


class UserUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin, UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = 'pages/user_auth/users/update.html'
    permission_required = 'auth.change_user'
    success_url = reverse_lazy('user_auth:users_list')
    url_redirect = success_url

    def get_object(self):
        uuid = self.kwargs.get('uuid')
        profile = get_object_or_404(Profile, uuid=uuid)
        return profile.user

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = self.get_object()
        return kwargs

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if not self.request.user.is_superuser:
            # is_staff/is_superuser solo los gestiona un superusuario: sin esta
            # guarda, un no-superusuario con auth.change_user podía auto-escalarse
            # enviando is_superuser=on en su propio formulario.
            form.fields.pop('is_staff', None)
            form.fields.pop('is_superuser', None)
        return form

    def form_valid(self, form):
        user = self.get_object()
        old_group_names = {g.name for g in user.groups.all()}
        new_group_names = {g.name for g in form.cleaned_data.get('groups', [])}

        if (
            CLIENTES_GROUP_NAME in old_group_names
            and CLIENTES_GROUP_NAME not in new_group_names
            and hasattr(user, 'commercial_customer')
        ):
            form.add_error(
                'groups',
                (
                    f'No puede quitar el grupo "{CLIENTES_GROUP_NAME}" a un usuario que tiene '
                    'perfil de cliente. Desactive el cliente desde el listado de clientes '
                    'si es necesario.'
                ),
            )
            return self.form_invalid(form)

        response = super().form_valid(form)
        user = self.object

        if (
            CLIENTES_GROUP_NAME not in old_group_names
            and CLIENTES_GROUP_NAME in new_group_names
            and not hasattr(user, 'commercial_customer')
        ):
            log_action(
                user=self.request.user,
                obj=user,
                action_flag=CHANGE,
                message=(
                    f'Se asignó el grupo {CLIENTES_GROUP_NAME} a {user.username}. '
                    'Redirigiendo a completar datos.'
                ),
                request=self.request,
            )
            messages.info(
                self.request, 'Complete los datos del cliente para este usuario.', extra_tags='info'
            )
            return redirect('commercial:cliente_create_for_user', user_uuid=user.profile.uuid)

        log_action(
            user=self.request.user,
            obj=self.object,
            action_flag=CHANGE,
            message=f'Se editó el perfil de {self.object.username}.',
            request=self.request,
        )

        messages.success(
            self.request, 'El usuario ha sido actualizado con éxito.', extra_tags='success'
        )
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Actualizar Usuario'
        context['parent'] = 'user_auth'
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
            messages.error(
                request,
                f'No se puede eliminar el usuario {user.username} si es el único superusuario.',
            )
            return redirect('user_auth:users_list')
        log_action(
            user=self.request.user,
            obj=user,
            action_flag=DELETION,
            message=f'Se eliminó al usuario {user.username}.',
            request=self.request,
        )
        user.delete()
        messages.success(request, f'Usuario {user.username} se ha eliminado correctamente.')
        return redirect('user_auth:users_list')


class CustomerRegisterView(CreateView):
    form_class = CustomerSignUpForm
    template_name = 'pages/user_auth/login/register.html'
    success_url = reverse_lazy('home:services_commercial_public')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, 'Ya tienes una sesión activa.')
            return redirect('home:services_commercial_public')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        try:
            with transaction.atomic():
                user = form.save()
        except IntegrityError:
            messages.error(
                self.request,
                'No se pudo completar el registro: los datos aportados ya están en uso. '
                'Revise usuario, correo, REEUP o NIT e intente de nuevo.',
            )
            return self.form_invalid(form)

        # backend explícito: con LDAP configurado (multiple backends) Django 5.2
        # exige conocer el backend o lanza ValueError → 500 en el registro público.
        login(
            self.request,
            user,
            backend='django.contrib.auth.backends.ModelBackend',
        )

        customer = None
        try:
            customer = Customer.objects.get(user=user)
            log_action(
                user=user,
                obj=customer,
                action_flag=ADDITION,
                message=f'Cliente registrado desde formulario público: {customer}.',
                request=self.request,
            )
        except Customer.DoesNotExist:
            pass

        welcome_msg = f'¡Registro exitoso{", " + str(customer) if customer else ""}! '
        messages.success(
            self.request,
            welcome_msg + 'Ahora puedes acceder a tus servicios comerciales.',
            extra_tags='success',
        )
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Registro Clientes'
        context['parent'] = ''
        context['segment'] = 'registro'
        context['is_registration'] = True
        return context
