from django.contrib import messages
from django.contrib.admin.models import LogEntry
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from django.views.generic import DetailView, UpdateView

from accounts.forms.profile.form import ProfileForm
from accounts.models import Profile

from django.contrib.admin.models import CHANGE
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
        
        # Obtener los últimos 10 registros de LogEntry para el usuario actual
        log_entries = LogEntry.objects.filter(user=self.request.user).order_by('-action_time')[:5]
        context['log_entries'] = log_entries
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
        return self.get_object().user == self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Editar Perfil'
        context['parent'] = 'accounts'
        context['segment'] = 'profile'
        context['url_list'] = self.success_url
        return context

    def post(self, request, *args, **kwargs):
        profile = self.get_object()

        # Registro de acción para eliminar el avatar
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
            return self.form_valid(self.get_form())

        # Registro de acción para actualizar el perfil
        response = super().post(request, *args, **kwargs)
        log_action(
            user=request.user,
            obj=profile,
            action_flag=CHANGE,
            message="El usuario actualizó su perfil."
        )
        messages.success(self.request, 'El perfil ha sido actualizado con éxito.', extra_tags='warning')
        return response
