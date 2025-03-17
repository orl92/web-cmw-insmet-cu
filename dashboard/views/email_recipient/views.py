from django.contrib import messages
from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin,
                                        UserPassesTestMixin)
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from core import settings
from dashboard.forms.email_recipient.forms import EmailRecipientFormSet, EmailRecipientListForm
from dashboard.models import EmailRecipientList

from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from common.utils import log_action

class EmailRecipientListListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    template_name = 'pages/dashboard/email_recipient/listado_correos.html'
    model = EmailRecipientList
    permission_required = 'dashboard.view_email_recipient_list'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Listados de Correos'
        context['segment'] = 'listado_correos'
        context['btn'] = 'Añadir Listado'
        context['url_create'] = reverse_lazy('crear_listado_correo')
        context['url_list'] = reverse_lazy('listado_correos')
        context['objects'] = EmailRecipientList.objects.all()
        return context

class EmailRecipientListCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = EmailRecipientList
    form_class = EmailRecipientListForm
    template_name = 'pages/dashboard/email_recipient/crear_listado_correo.html'
    permission_required = 'dashboard.add_email_recipient_list'
    success_url = reverse_lazy('listado_correos')

    def form_valid(self, form):
        print("Datos enviados (POST):", self.request.POST)  # Verifica los datos enviados
        response = super().form_valid(form)
        formset = EmailRecipientFormSet(self.request.POST, instance=self.object, prefix='recipients')

        if formset.is_valid():
            formset.save()
            # Registrar la acción
            log_action(
                user=self.request.user,
                obj=self.object,
                action_flag=ADDITION,
                message=f"Se creó un nuevo listado de correos: {self.object.name}."
            )
            messages.success(self.request, 'La lista de correos y los destinatarios se han creado con éxito.')
        else:
            print("Errores del formset:", formset.errors)  # Inspecciona los errores
            messages.error(self.request, 'Hubo un error con los destinatarios. Verifica los campos.')
            return self.render_to_response(self.get_context_data(form=form, formset=formset))
        
        if not formset.is_valid():
            print("Errores:", formset.errors)

        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['formset'] = kwargs.get('formset', EmailRecipientFormSet())
        context['formset'] = kwargs.get('formset', EmailRecipientFormSet(instance=self.object, prefix='recipients'))
        context['title'] = 'Crear Listado de Correos'
        context['parent'] = ''
        context['segment'] = 'email'
        context['url_list'] = reverse_lazy('listado_correos')
        return context

class EmailRecipientListUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin, UpdateView):
    model = EmailRecipientList
    form_class = EmailRecipientListForm
    template_name = 'pages/dashboard/email_recipient/actualizar_listado_correo.html'
    permission_required = 'dashboard.change_email_recipient_list'
    success_url = reverse_lazy('listado_correos')

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
            # Renderizar nuevamente si hay errores
            print(formset.errors)  # Depuración
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
        context['url_list'] = reverse_lazy('listado_correos')
        return context

    def test_func(self):
        # Verifica si el usuario es superusuario o si es el creador del listado
        listado = self.get_object()
        return self.request.user.is_superuser or listado.user == self.request.user

class EmailRecipientListDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = EmailRecipientList
    template_name = 'pages/dashboard/email_recipient/eliminar_listado_correo.html'
    permission_required = 'dashboard.delete_email_recipient_list'
    success_url = reverse_lazy('listado_correos')

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(EmailRecipientList, uuid=uuid)

    def post(self, request, *args, **kwargs):
        listado = self.get_object()
        
        # Registro de acción antes de eliminar
        log_action(
            user=self.request.user,
            obj=listado,
            action_flag=DELETION,
            message=f"Se eliminó el listado de correo: {listado.name}."
        )
        
        try:
            listado.delete()
            messages.success(request, 'El listado de correos ha sido eliminado con éxito.', extra_tags='danger')
        except Exception as e:
            messages.error(request, f'Error al eliminar el listado de correos: {str(e)}', extra_tags='danger')
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Eliminar Listado de Correos'
        context['parent'] = ''
        context['segment'] = 'email'
        context['url_list'] = reverse_lazy('listado_correos')
        return context
