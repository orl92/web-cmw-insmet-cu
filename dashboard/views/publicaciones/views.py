import base64
import os
from io import BytesIO

import xhtml2pdf.pisa as pisa
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UserPassesTestMixin)
from django.db import transaction
from django.forms import modelformset_factory
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import get_template
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DetailView,
    ListView,
    UpdateView,
    View,
)

from common.utils import SearchMixin, log_action
from dashboard.forms.publicaciones.forms import (
    CoauthorForm,
    ScientificPublicationForm)
from dashboard.models import Author, ScientificPublication


def get_coauthor_formset(queryset=None, data=None, prefix="coauthors"):
    """Retorna un formset para coautores con extra=0 (sin filas vacías por defecto)"""
    FormSet = modelformset_factory(
        Author,
        form=CoauthorForm,
        extra=0,
        can_delete=True)

    if data is not None:
        return FormSet(data=data, queryset=queryset, prefix=prefix)
    return FormSet(queryset=queryset, prefix=prefix)


class ScientificPublicationListView(
    LoginRequiredMixin, PermissionRequiredMixin, SearchMixin, ListView
):
    template_name = "pages/dashboard/publicaciones/listado_publicaciones.html"
    model = ScientificPublication
    context_object_name = "objects"
    permission_required = "dashboard.view_scientific_publication"
    search_fields = ['title', 'summary', 'author__first_name', 'author__last_name']

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.prefetch_related("author", "coauthors")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Listado de Publicaciones Científicas"
        context["parent"] = ""
        context["segment"] = "publicaciones"
        context["btn"] = "Añadir Publicación"
        context["url_create"] = reverse_lazy("crear_publicacion")
        context["url_list"] = reverse_lazy("listado_publicaciones")
        context['is_staff'] = self.request.user.is_staff or self.request.user.is_superuser
        context['is_superuser'] = self.request.user.is_superuser
        return context


class ScientificPublicationCreateView(
    LoginRequiredMixin, PermissionRequiredMixin, CreateView
):
    model = ScientificPublication
    form_class = ScientificPublicationForm
    template_name = "pages/dashboard/publicaciones/crear_publicacion.html"
    permission_required = "dashboard.add_scientific_publication"
    success_url = reverse_lazy("listado_publicaciones")
    url_redirect = success_url

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.POST:
            context["formset"] = get_coauthor_formset(
                data=self.request.POST,
                queryset=Author.objects.none(),
                prefix="coauthors")
        else:
            context["formset"] = get_coauthor_formset(
                queryset=Author.objects.none(), prefix="coauthors"
            )

        context["title"] = "Añadir Publicación Científica"
        context["parent"] = ""
        context["segment"] = "publicaciones"
        context["url_list"] = reverse_lazy("listado_publicaciones")
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context["formset"]

        # Validar ambos formularios
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    # Guardar la publicación principal
                    self.object = form.save(commit=False)
                    self.object.user = self.request.user
                    self.object.save()

                    # Procesar coautores
                    coauthors_to_add = []
                    for coauthor_form in formset:
                        if (
                            coauthor_form.cleaned_data
                            and not coauthor_form.cleaned_data.get("DELETE")
                        ):
                            # Solo procesar si tiene datos
                            if coauthor_form.cleaned_data.get(
                                "first_name"
                            ) and coauthor_form.cleaned_data.get("last_name"):
                                coauthor = coauthor_form.save()
                                if coauthor and coauthor != self.object.author:
                                    coauthors_to_add.append(coauthor)

                    # Añadir coautores a la publicación
                    if coauthors_to_add:
                        self.object.coauthors.add(*coauthors_to_add)

                    # Registrar la acción
                    log_action(
                        user=self.request.user,
                        obj=self.object,
                        action_flag=ADDITION,
                        message=f"Se creó una nueva publicación científica: {self.object.title}.")

                    messages.success(
                        self.request,
                        "La publicación científica se ha creado con éxito.",
                        extra_tags="success")

                    return super().form_valid(form)

            except Exception as e:
                messages.error(
                    self.request,
                    f"Error al guardar: {str(e)}",
                    extra_tags="danger")
                return self.render_to_response(
                    self.get_context_data(form=form, formset=formset)
                )
        else:
            # Mostrar errores
            messages.error(
                self.request,
                "Por favor, corrige los errores en el formulario.",
                extra_tags="danger")
            return self.render_to_response(
                self.get_context_data(form=form, formset=formset)
            )


class ScientificPublicationUpdateView(
    LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin, UpdateView
):
    model = ScientificPublication
    form_class = ScientificPublicationForm
    template_name = "pages/dashboard/publicaciones/actualizar_publicacion.html"
    permission_required = "dashboard.change_scientific_publication"
    success_url = reverse_lazy("listado_publicaciones")
    url_redirect = success_url

    def get_object(self, queryset=None):
        uuid = self.kwargs.get("uuid")
        return get_object_or_404(ScientificPublication, uuid=uuid)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Obtener coautores existentes de la publicación
        if self.object:
            coauthors_queryset = self.object.coauthors.all()
        else:
            coauthors_queryset = Author.objects.none()

        if self.request.POST:
            formset = get_coauthor_formset(
                data=self.request.POST,
                queryset=coauthors_queryset,
                prefix="coauthors")
        else:
            formset = get_coauthor_formset(
                queryset=coauthors_queryset, prefix="coauthors"
            )

        context["formset"] = formset
        context["title"] = "Actualizar Publicación Científica"
        context["parent"] = ""
        context["segment"] = "publicaciones"
        context["url_list"] = reverse_lazy("listado_publicaciones")
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context["formset"]

        # Validar ambos formularios
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    # Guardar la publicación principal
                    self.object = form.save()

                    # Procesar coautores
                    coauthors_to_keep = []
                    for coauthor_form in formset:
                        if coauthor_form.cleaned_data:
                            if coauthor_form.cleaned_data.get("DELETE"):
                                # Solo marcar para eliminación de la relación
                                pass
                            else:
                                # Solo procesar si tiene datos
                                if coauthor_form.cleaned_data.get(
                                    "first_name"
                                ) and coauthor_form.cleaned_data.get("last_name"):
                                    coauthor = coauthor_form.save()
                                    if coauthor and coauthor != self.object.author:
                                        coauthors_to_keep.append(coauthor)

                    # Actualizar relación de coautores
                    self.object.coauthors.set(coauthors_to_keep)

                    # Registrar acción
                    log_action(
                        user=self.request.user,
                        obj=self.object,
                        action_flag=CHANGE,
                        message=f"Se actualizó la publicación científica: {self.object.title}.")

                    messages.success(
                        self.request,
                        "La publicación científica ha sido actualizada con éxito.")

                    return super().form_valid(form)

            except Exception as e:
                messages.error(
                    self.request,
                    f"Error al guardar: {str(e)}",
                    extra_tags="danger")
                return self.render_to_response(
                    self.get_context_data(form=form, formset=formset)
                )
        else:
            # Mostrar errores específicos
            if not formset.is_valid():
                for form in formset:
                    if form.errors:
                        for field, errors in form.errors.items():
                            for error in errors:
                                messages.error(
                                    self.request,
                                    f"Error en coautor: {error}",
                                    extra_tags="danger")

            messages.error(
                self.request,
                "Por favor, corrige los errores en el formulario.",
                extra_tags="danger")
            return self.render_to_response(
                self.get_context_data(form=form, formset=formset)
            )

    def test_func(self):
        """
        Verificar permisos adicionales.
        """
        return self.request.user.is_superuser


class ScientificPublicationDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'dashboard.delete_scientific_publication'

    def post(self, request, uuid):
        publicacion = get_object_or_404(ScientificPublication, uuid=uuid)
        log_action(
            user=self.request.user,
            obj=publicacion,
            action_flag=DELETION,
            message=f"Se eliminó la publicación científica: {publicacion.title}."
        )
        try:
            publicacion.delete()
            messages.success(request, 'La publicación científica ha sido eliminada con éxito.')
        except Exception as e:
            messages.error(request, f'Error al eliminar la publicación científica: {str(e)}')
        return redirect('listado_publicaciones')

class ScientificPublicationDetailView(
    LoginRequiredMixin, PermissionRequiredMixin, DetailView
):
    model = ScientificPublication
    template_name = "pages/dashboard/publicaciones/detalle_publicacion.html"
    permission_required = "dashboard.view_scientific_publication"
    context_object_name = "publicacion"

    def get_object(self, queryset=None):
        uuid = self.kwargs.get("uuid")
        return get_object_or_404(ScientificPublication, uuid=uuid)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Detalle de la Publicación Científica"
        context["parent"] = ""
        context["segment"] = "publicaciones"
        context["url_list"] = reverse_lazy("listado_publicaciones")
        # Prefetch related authors for better performance
        context["publicacion"] = ScientificPublication.objects.prefetch_related(
            "author", "coauthors"
        ).get(uuid=self.kwargs.get("uuid"))
        return context


class ScientificPublicationPDFView(
    LoginRequiredMixin, PermissionRequiredMixin, DetailView
):
    model = ScientificPublication
    permission_required = "dashboard.view_scientific_publication"

    def get(self, request, *args, **kwargs):
        publicacion = self.get_object()

        # Obtener imagen en formato Base64
        logo_path = os.path.join(settings.BASE_DIR, "static/dist/img/logo.png")
        logo_base64 = self.get_image_base64(logo_path)

        # Renderizar template HTML
        template = get_template("pages/dashboard/publicaciones/pdf_template.html")
        context = {
            "publicacion": publicacion,
            "logo_base64": logo_base64,
            "author": publicacion.author,
            "coauthors": publicacion.coauthors.all(),
        }
        html = template.render(context)

        # Crear PDF
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)

        if not pdf.err:
            response = HttpResponse(result.getvalue(), content_type="application/pdf")
            filename = f"publicacion_{publicacion.title[:50]}_{publicacion.publication_date.strftime('%Y-%m-%d')}.pdf"
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            return response
        return HttpResponse("Error al generar el PDF", status=400)

    def get_object(self, queryset=None):
        uuid = self.kwargs.get("uuid")
        return get_object_or_404(ScientificPublication, uuid=uuid)

    @staticmethod
    def get_image_base64(image_path):
        """Convierte la imagen en Base64."""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode("utf-8")
        except FileNotFoundError:
            return ""
