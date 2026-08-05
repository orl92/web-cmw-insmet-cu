from django.contrib import messages
from django.contrib.admin.models import CHANGE, LogEntry
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import DetailView, UpdateView

from apps.core.utils import log_action
from apps.user_auth.forms.profile import ProfileForm
from apps.user_auth.models import Profile


class ProfileDetailView(LoginRequiredMixin, DetailView):
    template_name = 'pages/user_auth/profile/profile.html'
    model = User

    def get_object(self, **kwargs):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Perfil de Usuario'
        context['parent'] = 'user_auth'
        context['segment'] = 'profile'
        context['btn'] = 'Editar Perfil'
        context['objects'] = User.objects.all()

        log_entries = LogEntry.objects.filter(user=self.request.user).order_by('-action_time')
        paginator = Paginator(log_entries, 4)
        page_number = self.request.GET.get('page')
        context['log_entries_page'] = paginator.get_page(page_number)
        context['is_ldap'] = getattr(self.request.user.profile, 'is_ldap', False)

        return context


class ProfileUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Profile
    form_class = ProfileForm
    template_name = 'pages/user_auth/profile/update.html'
    success_url = reverse_lazy('user_auth:profile_detail')
    url_redirect = success_url

    def get_object(self, **kwargs):
        return get_object_or_404(Profile, user=self.request.user)

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
        context['parent'] = 'user_auth'
        context['segment'] = 'profile'
        context['url_list'] = self.success_url
        context['is_customer'] = hasattr(self.request.user, 'commercial_customer')
        context['client_type'] = (
            self.request.user.commercial_customer.client_type
            if hasattr(self.request.user, 'commercial_customer')
            else None
        )

        active_tab = 'personal'

        if self.request.method == 'POST':
            form = context.get('form')
            if form and form.errors:
                campos_personal = ['first_name', 'last_name', 'email', 'newsletter', 'avatar']
                campos_cliente = ['company_name', 'reeup', 'nit', 'account', 'address', 'phone']

                if any(campo in form.errors for campo in campos_personal):
                    active_tab = 'personal'
                elif any(campo in form.errors for campo in campos_cliente):
                    active_tab = 'cliente'

        context['active_tab'] = active_tab
        return context

    def post(self, request, *args, **kwargs):
        if 'delete_avatar' in request.POST:
            profile = self.get_object()
            profile.avatar.delete(save=False)
            profile.save()
            log_action(
                user=request.user,
                obj=profile,
                action_flag=CHANGE,
                message='El usuario eliminó su avatar.',
            )
            messages.success(
                self.request, 'El avatar ha sido eliminado con éxito.', extra_tags='danger'
            )
            return redirect('user_auth:profile_update')

        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        profile = self.object

        log_action(
            user=self.request.user,
            obj=profile,
            action_flag=CHANGE,
            message='El usuario actualizó su perfil.',
        )

        if hasattr(self.request.user, 'commercial_customer'):
            log_action(
                user=self.request.user,
                obj=self.request.user.commercial_customer,
                action_flag=CHANGE,
                message='El cliente actualizó sus datos de empresa.',
            )

        messages.success(
            self.request, 'El perfil ha sido actualizado con éxito.', extra_tags='warning'
        )
        return response
