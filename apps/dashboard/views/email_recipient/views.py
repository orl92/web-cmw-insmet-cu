import logging

from django.contrib import messages
from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UserPassesTestMixin,
)
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView, View

from apps.common.utils import log_action
from apps.dashboard.forms.email_recipient.forms import (
    EmailRecipientFormSet,
    EmailRecipientListForm,
)
from apps.dashboard.models import EmailRecipientList

logger = logging.getLogger(__name__)



class EmailRecipientListListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    template_name = 'pages/dashboard/email_recipient/listado_correos.html'
    model = EmailRecipientList
    permission_required = 'dashboard.view_email_recipient_list'
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Listados de Correos'
        context['parent'] = ''
        context['segment'] = 'email'
        context['btn'] = 'Añadir Listado'
        context['url_create'] = reverse_lazy('dashboard:lista_correo_create')
        context['url_list'] = reverse_lazy('dashboard:lista_correo_list')
        context['is_superuser'] = self.request.user.is_superuser
        context['url_export'] = reverse_lazy('dashboard:lista_correo_export_csv')
        context['objects'] = EmailRecipientList.objects.all()
        return context

class EmailRecipientListCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = EmailRecipientList
    form_class = EmailRecipientListForm
    template_name = 'pages/dashboard/email_recipient/crear_listado_correo.html'
    permission_required = 'dashboard.add_email_recipient_list'
    success_url = reverse_lazy('dashboard:lista_correo_list')

    def form_valid(self, form):
        logger.debug("Datos enviados (POST): %s", self.request.POST)
        response = super().form_valid(form)
        formset = EmailRecipientFormSet(self.request.POST, instance=self.object, prefix='recipients')

        if formset.is_valid():
            formset.save()
            log_action(
                user=self.request.user,
                obj=self.object,
                action_flag=ADDITION,
                message=f"Se creó un nuevo listado de correos: {self.object.name}."
            )
            messages.success(self.request, 'La lista de correos y los destinatarios se han creado con éxito.')
        else:
            logger.debug("Errores del formset: %s", formset.errors)
            messages.error(self.request, 'Hubo un error con los destinatarios. Verifica los campos.')
            return self.render_to_response(self.get_context_data(form=form, formset=formset))

        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['formset'] = kwargs.get('formset', EmailRecipientFormSet(instance=self.object, prefix='recipients'))
        context['title'] = 'Crear Listado de Correos'
        context['parent'] = ''
        context['segment'] = 'email'
        context['url_list'] = reverse_lazy('dashboard:lista_correo_list')
        return context

class EmailRecipientListUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin, UpdateView):
    model = EmailRecipientList
    form_class = EmailRecipientListForm
    template_name = 'pages/dashboard/email_recipient/actualizar_listado_correo.html'
    permission_required = 'dashboard.change_email_recipient_list'
    success_url = reverse_lazy('dashboard:lista_correo_list')

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(EmailRecipientList, uuid=uuid)

    def form_valid(self, form):
        # Guardar cambios en la lista principal
        response = super().form_valid(form)
        formset = EmailRecipientFormSet(self.request.POST, instance=self.object, prefix='recipients')

        if formset.is_valid():
            formset.save()

            # Registrar acción
            log_action(
                user=self.request.user,
                obj=self.object,
                action_flag=CHANGE,
                message=f"Se actualizó el listado de correos: {self.object.name}."
            )

            messages.success(self.request, 'La lista de correos y los destinatarios han sido actualizados con éxito.')
        else:
            logger.debug("Errores del formset en update: %s", formset.errors)
            messages.error(self.request, 'Hubo un error con los destinatarios. Verifica los campos.')
            return self.render_to_response(self.get_context_data(form=form, formset=formset))

        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        formset = kwargs.get('formset', EmailRecipientFormSet(instance=self.object, prefix='recipients'))

        # Limpia los campos `None` en los formularios existentes y nuevos
        for form in formset:
            if not form.instance.email:  # Si el email es None o vacío
                form.initial['email'] = ''  # Asigna un valor inicial vacío

        context['formset'] = formset
        context['title'] = 'Actualizar Listado de Correos'
        context['parent'] = ''
        context['segment'] = 'email'
        context['url_list'] = reverse_lazy('dashboard:lista_correo_list')
        return context

    def test_func(self):
        return self.request.user.is_superuser

class EmailRecipientListDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'dashboard.delete_email_recipient_list'

    def post(self, request, uuid):
        email_list = get_object_or_404(EmailRecipientList, uuid=uuid)
        log_action(
            user=self.request.user,
            obj=email_list,
            action_flag=DELETION,
            message=f"Se eliminó el listado de correo {email_list.name}."
        )
        try:
            email_list.delete()
            messages.success(request, 'El listado de correo ha sido eliminado con éxito.')
        except Exception as e:
            messages.error(request, str(e))
        return redirect('dashboard:lista_correo_list')
