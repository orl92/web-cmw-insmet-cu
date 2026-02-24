from accounts.forms.profile.form import ProfileForm
from accounts.models import Profile
from common.utils import log_action
from django.contrib import messages
from django.contrib.admin.models import CHANGE, LogEntry
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import DetailView, UpdateView

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
        return context

    def post(self, request, *args, **kwargs):
        profile = self.get_object()

        # Acción de eliminar avatar (sin pasar por el formulario)
        if 'delete_avatar' in request.POST:
            profile.avatar.delete(save=False)
            profile.save()
            log_action(
                user=request.user,
                obj=profile,
                action_flag=CHANGE,
                message="El usuario eliminó su avatar."
            )
            messages.success(self.request, 'El avatar ha sido eliminado con éxito.', extra_tags='danger')
            # Redirigir a la misma página de edición (o a donde corresponda)
            return redirect('update_profile', uuid=profile.uuid)  # Ajusta el nombre de la URL si es necesario

        # Si no es eliminar avatar, procesar el formulario normalmente
        response = super().post(request, *args, **kwargs)
        log_action(
            user=request.user,
            obj=profile,
            action_flag=CHANGE,
            message="El usuario actualizó su perfil."
        )
        
        if hasattr(request.user, 'customer'):
            log_action(
                user=request.user,
                obj=request.user.customer,
                action_flag=CHANGE,
                message="El cliente actualizó sus datos de empresa."
            )
        
        messages.success(self.request, 'El perfil ha sido actualizado con éxito.', extra_tags='warning')
        return response

