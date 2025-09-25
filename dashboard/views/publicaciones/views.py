from django.contrib import messages
from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin,
                                        UserPassesTestMixin)
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView, DetailView

from dashboard.forms.publicaciones.forms import ScientificPublicationForm, AuthorFormSet
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
        context['objects'] = ScientificPublication.objects.all().prefetch_related('authors')
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
        self.object = form.save()

        # Procesar el formset de autores
        formset = AuthorFormSet(self.request.POST, prefix='authors')

        if formset.is_valid():
            authors = formset.save(commit=False)

            # Guardar cada autor y añadirlo a la publicación
            for author in authors:
                author.save()
                self.object.authors.add(author)

            # Guardar autores marcados para eliminar
            for form in formset.deleted_forms:
                if form.instance.pk:
                    author = form.instance
                    self.object.authors.remove(author)
                    # Opcional: eliminar el autor de la base de datos si no está en otras publicaciones
                    if author.publications.count() == 0:
                        author.delete()

            # Registrar la acción
            log_action(
                user=self.request.user,
                obj=self.object,
                action_flag=ADDITION,
                message=f"Se creó una nueva publicación científica: {self.object.title}."
            )

            messages.success(self.request, 'La publicación científica y los autores se han creado con éxito.',
                             extra_tags='success')
        else:
            # Mostrar errores del formset
            print("Errores del formset:", formset.errors)
            messages.error(self.request, 'Hubo un error con los autores. Verifica los campos.')
            return self.render_to_response(self.get_context_data(form=form, formset=formset))

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['formset'] = kwargs.get('formset', AuthorFormSet(queryset=Author.objects.none(), prefix='authors'))
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

        # Procesar el formset de autores
        formset = AuthorFormSet(self.request.POST, prefix='authors')

        if formset.is_valid():
            # Obtener autores actuales de la publicación
            current_authors = set(self.object.authors.all())
            new_authors = set()

            # Guardar nuevos autores y actualizar existentes
            for author_form in formset:
                if author_form.cleaned_data.get('DELETE') and author_form.instance.pk:
                    # Eliminar autor de la publicación
                    self.object.authors.remove(author_form.instance)
                    # Eliminar autor de la base de datos si no está en otras publicaciones
                    if author_form.instance.publications.count() == 0:
                        author_form.instance.delete()
                elif author_form.has_changed():
                    author = author_form.save()
                    new_authors.add(author)
                    self.object.authors.add(author)

            # Registrar acción
            log_action(
                user=self.request.user,
                obj=self.object,
                action_flag=CHANGE,
                message=f"Se actualizó la publicación científica: {self.object.title}."
            )

            messages.success(self.request, 'La publicación científica y los autores han sido actualizados con éxito.',
                             extra_tags='warning')
        else:
            # Renderizar nuevamente si hay errores
            print("Errores del formset:", formset.errors)
            messages.error(self.request, 'Hubo un error con los autores. Verifica los campos.')
            return self.render_to_response(self.get_context_data(form=form, formset=formset))

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Obtener autores existentes de la publicación
        if self.object:
            authors_queryset = self.object.authors.all()
        else:
            authors_queryset = Author.objects.none()

        formset = kwargs.get('formset', AuthorFormSet(queryset=authors_queryset, prefix='authors'))

        context['formset'] = formset
        context['title'] = 'Actualizar Publicación Científica'
        context['parent'] = ''
        context['segment'] = 'publicaciones'
        context['url_list'] = reverse_lazy('listado_publicaciones')
        return context

    def test_func(self):
        # Verifica si el usuario es superusuario o si es el creador de la publicación
        publicacion = self.get_object()
        return self.request.user.is_superuser or publicacion.user == self.request.user


# Las demás vistas (DeleteView, DetailView) permanecen igual...
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
        context['publicacion'] = ScientificPublication.objects.prefetch_related('authors').get(
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
            'authors': publicacion.authors.all()
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