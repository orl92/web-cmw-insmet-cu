from django.contrib import messages
from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin,
                                        UserPassesTestMixin)
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView, DetailView

from dashboard.forms.publicaciones.forms import ScientificPublicationForm, CoauthorFormSet
from dashboard.models import ScientificPublication, Author

from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from common.utils import log_action

import base64
import os
from django.http import HttpResponse
from django.template.loader import get_template
from io import BytesIO
import xhtml2pdf.pisa as pisa
from django.conf import settings


class ScientificPublicationListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    template_name = 'pages/dashboard/publicaciones/listado_publicaciones.html'
    model = ScientificPublication
    permission_required = 'dashboard.view_scientific_publication'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Listado de Publicaciones Científicas'
        context['parent'] = ''
        context['segment'] = 'publicaciones'
        context['btn'] = 'Añadir Publicación'
        context['url_create'] = reverse_lazy('crear_publicacion')
        context['url_list'] = reverse_lazy('listado_publicaciones')
        context['objects'] = ScientificPublication.objects.all().prefetch_related('author', 'coauthors')
        return context


class ScientificPublicationCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = ScientificPublication
    form_class = ScientificPublicationForm
    template_name = 'pages/dashboard/publicaciones/crear_publicacion.html'
    permission_required = 'dashboard.add_scientific_publication'
    success_url = reverse_lazy('listado_publicaciones')
    url_redirect = success_url

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        # Guardar la publicación principal primero
        self.object = form.save(commit=False)
        self.object.user = self.request.user
        self.object.save()

        # Procesar el formset de coautores
        formset = CoauthorFormSet(self.request.POST, prefix='coauthors')

        if formset.is_valid():
            # Guardar coautores
            coauthors = []
            for coauthor_form in formset:
                if coauthor_form.cleaned_data and not coauthor_form.cleaned_data.get('DELETE'):
                    coauthor = coauthor_form.save()
                    if coauthor and coauthor != self.object.author:  # No añadir el autor como coautor
                        coauthors.append(coauthor)

            # Añadir coautores a la publicación
            for coauthor in coauthors:
                self.object.coauthors.add(coauthor)

            # Registrar la acción
            log_action(
                user=self.request.user,
                obj=self.object,
                action_flag=ADDITION,
                message=f"Se creó una nueva publicación científica: {self.object.title}."
            )

            messages.success(self.request, 'La publicación científica se ha creado con éxito.', extra_tags='success')
        else:
            # Mostrar errores del formset
            print("Errores del formset:", formset.errors)
            messages.error(self.request, 'Hubo un error con los coautores. Verifica los campos.')
            return self.render_to_response(self.get_context_data(form=form, formset=formset))

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['formset'] = kwargs.get('formset', CoauthorFormSet(queryset=Author.objects.none(), prefix='coauthors'))
        context['title'] = 'Añadir Publicación Científica'
        context['parent'] = ''
        context['segment'] = 'publicaciones'
        context['url_list'] = reverse_lazy('listado_publicaciones')
        return context


class ScientificPublicationUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin, UpdateView):
    model = ScientificPublication
    form_class = ScientificPublicationForm
    template_name = 'pages/dashboard/publicaciones/actualizar_publicacion.html'
    permission_required = 'dashboard.change_scientific_publication'
    success_url = reverse_lazy('listado_publicaciones')
    url_redirect = success_url

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(ScientificPublication, uuid=uuid)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        # Guardar cambios en la publicación principal
        self.object = form.save()

        # Procesar el formset de coautores
        formset = CoauthorFormSet(self.request.POST, prefix='coauthors')

        if formset.is_valid():
            # Limpiar coautores actuales
            self.object.coauthors.clear()

            # Guardar nuevos coautores
            coauthors = []
            for coauthor_form in formset:
                if coauthor_form.cleaned_data and not coauthor_form.cleaned_data.get('DELETE'):
                    coauthor = coauthor_form.save()
                    if coauthor and coauthor != self.object.author:  # No añadir el autor como coautor
                        coauthors.append(coauthor)

            # Añadir coautores a la publicación
            for coauthor in coauthors:
                self.object.coauthors.add(coauthor)

            # Registrar acción
            log_action(
                user=self.request.user,
                obj=self.object,
                action_flag=CHANGE,
                message=f"Se actualizó la publicación científica: {self.object.title}."
            )

            messages.success(self.request, 'La publicación científica ha sido actualizada con éxito.',
                             extra_tags='warning')
        else:
            # Renderizar nuevamente si hay errores
            print("Errores del formset:", formset.errors)
            messages.error(self.request, 'Hubo un error con los coautores. Verifica los campos.')
            return self.render_to_response(self.get_context_data(form=form, formset=formset))

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Obtener coautores existentes de la publicación
        if self.object:
            coauthors_queryset = self.object.coauthors.all()
        else:
            coauthors_queryset = Author.objects.none()

        formset = kwargs.get('formset', CoauthorFormSet(queryset=coauthors_queryset, prefix='coauthors'))

        context['formset'] = formset
        context['title'] = 'Actualizar Publicación Científica'
        context['parent'] = ''
        context['segment'] = 'publicaciones'
        context['url_list'] = reverse_lazy('listado_publicaciones')
        return context

    def test_func(self):
        publicacion = self.get_object()
        return self.request.user.is_superuser or publicacion.user == self.request.user


class ScientificPublicationDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = ScientificPublication
    template_name = 'pages/dashboard/publicaciones/eliminar_publicacion.html'
    permission_required = 'dashboard.delete_scientific_publication'
    success_url = reverse_lazy('listado_publicaciones')
    url_redirect = success_url

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(ScientificPublication, uuid=uuid)

    def post(self, request, *args, **kwargs):
        publicacion = self.get_object()

        # Registro de acción antes de eliminar
        log_action(
            user=self.request.user,
            obj=publicacion,
            action_flag=DELETION,
            message=f"Se eliminó la publicación científica: {publicacion.title}."
        )

        try:
            publicacion.delete()
            messages.success(request, 'La publicación científica ha sido eliminada con éxito.', extra_tags='danger')
        except Exception as e:
            messages.error(request, f'Error al eliminar la publicación científica: {str(e)}', extra_tags='danger')
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Eliminar Publicación Científica'
        context['parent'] = ''
        context['segment'] = 'publicaciones'
        context['url_list'] = reverse_lazy('listado_publicaciones')
        return context


class ScientificPublicationDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = ScientificPublication
    template_name = 'pages/dashboard/publicaciones/detalle_publicacion.html'
    permission_required = 'dashboard.view_scientific_publication'
    context_object_name = 'publicacion'

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(ScientificPublication, uuid=uuid)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Detalle de la Publicación Científica'
        context['parent'] = ''
        context['segment'] = 'publicaciones'
        context['url_list'] = reverse_lazy('listado_publicaciones')
        # Prefetch related authors for better performance
        context['publicacion'] = ScientificPublication.objects.prefetch_related('author', 'coauthors').get(
            uuid=self.kwargs.get('uuid'))
        return context


class ScientificPublicationPDFView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = ScientificPublication
    permission_required = 'dashboard.view_scientific_publication'

    def get(self, request, *args, **kwargs):
        publicacion = self.get_object()

        # Obtener imagen en formato Base64
        logo_path = os.path.join(settings.BASE_DIR, "static/dist/img/logo.png")
        logo_base64 = self.get_image_base64(logo_path)

        # Renderizar template HTML
        template = get_template('pages/dashboard/publicaciones/pdf_template.html')
        context = {
            'publicacion': publicacion,
            'logo_base64': logo_base64,
            'author': publicacion.author,
            'coauthors': publicacion.coauthors.all()
        }
        html = template.render(context)

        # Crear PDF
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)

        if not pdf.err:
            response = HttpResponse(result.getvalue(), content_type='application/pdf')
            filename = f"publicacion_{publicacion.title[:50]}_{publicacion.publication_date.strftime('%Y-%m-%d')}.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        return HttpResponse("Error al generar el PDF", status=400)

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(ScientificPublication, uuid=uuid)

    @staticmethod
    def get_image_base64(image_path):
        """Convierte la imagen en Base64."""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode("utf-8")
        except FileNotFoundError:
            return ""