from django.contrib import messages
from django.contrib.admin.models import CHANGE, LogEntry
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import DetailView, UpdateView

from accounts.forms.profile.form import ProfileForm
from accounts.models import Profile
from common.utils import log_action

# Create your views here.


class ProfileDetailView(LoginRequiredMixin, DetailView):
    template_name = 'pages/accounts/profile/profile.html'
    model = User

    def get_object(self, **kwargs):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Perfil de Usuario'
        context['parent'] = 'accounts'
        context['segment'] = 'profile'
        context['btn'] = 'Editar Perfil'
        context['objects'] = User.objects.all()

        # Obtener todos los registros de LogEntry para el usuario actual
        log_entries = LogEntry.objects.filter(user=self.request.user).order_by('-action_time')

        # Configurar paginación
        paginator = Paginator(log_entries, 4)  # Mostrar 4 registros por página
        page_number = self.request.GET.get('page')  # Obtener el número de página de la solicitud
        context['log_entries_page'] = paginator.get_page(page_number)  # Pasar la página actual al contexto
        context['is_ldap'] = getattr(self.request.user.profile, 'is_ldap', False)

        return context


class ProfileUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Profile
    form_class = ProfileForm
    template_name = 'pages/accounts/profile/profile_update.html'
    success_url = reverse_lazy('profile')
    url_redirect = success_url

    def get_object(self, **kwargs):
        return Profile.objects.get(uuid=self.kwargs['uuid'])

    def get_initial(self):
        initial = super().get_initial()
        user = self.request.user
        initial['first_name'] = user.first_name
        initial['last_name'] = user.last_name
        initial['email'] = user.email
        return initial

    def test_func(self):
        profile = self.get_object()
        return profile.user_id is not None and profile.user == self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Editar Perfil'
        context['parent'] = 'accounts'
        context['segment'] = 'profile'
        context['url_list'] = self.success_url
        context['is_customer'] = hasattr(self.request.user, 'customer')

        # --- Lógica para seleccionar la pestaña activa según errores ---
        active_tab = 'personal'  # valor por defecto

        if self.request.method == 'POST':
            form = context.get('form')
            if form and form.errors:
                # Definir qué campos pertenecen a cada pestaña
                campos_personal = ['first_name', 'last_name', 'email', 'avatar']
                campos_empresa = ['company_name', 'reeup', 'nit', 'account', 'address', 'phone', 'newsletter']
                
                # Prioridad: si hay error en personal, mostramos personal
                if any(campo in form.errors for campo in campos_personal):
                    active_tab = 'personal'
                # Si no hay error en personal pero sí en empresa, mostramos empresa
                elif any(campo in form.errors for campo in campos_empresa):
                    active_tab = 'empresa'
                # Si no hay errores (caso improbable aquí), se queda 'personal'

        context['active_tab'] = active_tab
        return context

    def post(self, request, *args, **kwargs):
        # Manejar eliminación de avatar (no pasa por el formulario)
        if 'delete_avatar' in request.POST:
            profile = self.get_object()
            profile.avatar.delete(save=False)
            profile.save()
            log_action(
                user=request.user,
                obj=profile,
                action_flag=CHANGE,
                message="El usuario eliminó su avatar."
            )
            messages.success(self.request, 'El avatar ha sido eliminado con éxito.', extra_tags='danger')
            return redirect('update_profile', uuid=profile.uuid)

        # Si no es eliminar avatar, procesar normalmente
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        """Este método se llama solo cuando el formulario es válido"""
        response = super().form_valid(form)
        profile = self.object  # El perfil actualizado

        # Registrar acción de actualización de perfil
        log_action(
            user=self.request.user,
            obj=profile,
            action_flag=CHANGE,
            message="El usuario actualizó su perfil."
        )

        # Si es cliente, registrar también actualización de datos de empresa
        if hasattr(self.request.user, 'customer'):
            log_action(
                user=self.request.user,
                obj=self.request.user.customer,
                action_flag=CHANGE,
                message="El cliente actualizó sus datos de empresa."
            )

        # Mensaje de éxito (solo cuando todo está bien)
        messages.success(self.request, 'El perfil ha sido actualizado con éxito.', extra_tags='warning')
        return response
