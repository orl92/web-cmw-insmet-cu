from django.contrib import messages
from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UserPassesTestMixin,
)
from django.db import transaction
from django.forms import modelformset_factory
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    ListView,
    UpdateView,
    View,
)

from apps.core.utils import log_action
from apps.core.views import ServeModelFileView
from apps.publications.forms import CoauthorForm, ScientificPublicationForm
from apps.publications.models import Author, ScientificPublication


def get_coauthor_formset(queryset=None, data=None, prefix='coauthors'):
    formset_class = modelformset_factory(Author, form=CoauthorForm, extra=0, can_delete=True)

    if data is not None:
        return formset_class(data=data, queryset=queryset, prefix=prefix)
    return formset_class(queryset=queryset, prefix=prefix)


class ScientificPublicationListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    template_name = 'pages/publications/list.html'
    model = ScientificPublication
    permission_required = 'publications.view_scientific_publication'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Listado de Publicaciones Científicas'
        context['parent'] = ''
        context['segment'] = 'publicaciones'
        context['btn'] = 'Añadir Publicación'
        context['url_create'] = reverse_lazy('publications:create')
        context['url_list'] = reverse_lazy('publications:list')
        context['is_superuser'] = self.request.user.is_superuser
        context['objects'] = (
            ScientificPublication.objects.all()
            .select_related('author')
            .prefetch_related('coauthors')
        )
        return context


class ScientificPublicationCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = ScientificPublication
    form_class = ScientificPublicationForm
    template_name = 'pages/publications/create.html'
    permission_required = 'publications.add_scientific_publication'
    success_url = reverse_lazy('publications:list')
    url_redirect = success_url

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.POST:
            context['formset'] = get_coauthor_formset(
                data=self.request.POST, queryset=Author.objects.none(), prefix='coauthors'
            )
        else:
            context['formset'] = get_coauthor_formset(
                queryset=Author.objects.none(), prefix='coauthors'
            )

        context['title'] = 'Añadir Publicación Científica'
        context['parent'] = ''
        context['segment'] = 'publicaciones'
        context['url_list'] = reverse_lazy('publications:list')
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']

        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    self.object = form.save()

                    coauthors_to_add = []
                    for coauthor_form in formset:
                        if (
                            coauthor_form.cleaned_data
                            and not coauthor_form.cleaned_data.get('DELETE')
                            and coauthor_form.cleaned_data.get('first_name')
                            and coauthor_form.cleaned_data.get('last_name')
                        ):
                            coauthor = coauthor_form.save()
                            if coauthor and coauthor != self.object.author:
                                coauthors_to_add.append(coauthor)

                    if coauthors_to_add:
                        self.object.coauthors.add(*coauthors_to_add)

                    log_action(
                        user=self.request.user,
                        obj=self.object,
                        action_flag=ADDITION,
                        message=f'Se creó una nueva publicación científica: {self.object.title}.',
                    )

                    messages.success(
                        self.request,
                        'La publicación científica se ha creado con éxito.',
                        extra_tags='success',
                    )

                    return super().form_valid(form)

            except Exception as e:
                messages.error(self.request, f'Error al guardar: {str(e)}', extra_tags='danger')
                return self.render_to_response(self.get_context_data(form=form, formset=formset))
        else:
            messages.error(
                self.request,
                'Por favor, corrige los errores en el formulario.',
                extra_tags='danger',
            )
            return self.render_to_response(self.get_context_data(form=form, formset=formset))


class ScientificPublicationUpdateView(
    LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin, UpdateView
):
    model = ScientificPublication
    form_class = ScientificPublicationForm
    template_name = 'pages/publications/update.html'
    permission_required = 'publications.change_scientific_publication'
    success_url = reverse_lazy('publications:list')
    url_redirect = success_url

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(ScientificPublication, uuid=uuid)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        coauthors_queryset = self.object.coauthors.all() if self.object else Author.objects.none()

        if self.request.POST:
            formset = get_coauthor_formset(
                data=self.request.POST, queryset=coauthors_queryset, prefix='coauthors'
            )
        else:
            formset = get_coauthor_formset(queryset=coauthors_queryset, prefix='coauthors')

        context['formset'] = formset
        context['title'] = 'Actualizar Publicación Científica'
        context['parent'] = ''
        context['segment'] = 'publicaciones'
        context['url_list'] = reverse_lazy('publications:list')
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']

        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    self.object = form.save()

                    coauthors_to_keep = []
                    for coauthor_form in formset:
                        if coauthor_form.cleaned_data:
                            if coauthor_form.cleaned_data.get('DELETE'):
                                pass
                            else:
                                if coauthor_form.cleaned_data.get(
                                    'first_name'
                                ) and coauthor_form.cleaned_data.get('last_name'):
                                    coauthor = coauthor_form.save()
                                    if coauthor and coauthor != self.object.author:
                                        coauthors_to_keep.append(coauthor)

                    self.object.coauthors.set(coauthors_to_keep)

                    log_action(
                        user=self.request.user,
                        obj=self.object,
                        action_flag=CHANGE,
                        message=f'Se actualizó la publicación científica: {self.object.title}.',
                    )

                    messages.success(
                        self.request, 'La publicación científica ha sido actualizada con éxito.'
                    )

                    return super().form_valid(form)

            except Exception as e:
                messages.error(self.request, f'Error al guardar: {str(e)}', extra_tags='danger')
                return self.render_to_response(self.get_context_data(form=form, formset=formset))
        else:
            if not formset.is_valid():
                for form in formset:
                    if form.errors:
                        for _field, errors in form.errors.items():
                            for error in errors:
                                messages.error(
                                    self.request, f'Error en coautor: {error}', extra_tags='danger'
                                )

            messages.error(
                self.request,
                'Por favor, corrige los errores en el formulario.',
                extra_tags='danger',
            )
            return self.render_to_response(self.get_context_data(form=form, formset=formset))

    def test_func(self):
        return self.request.user.is_superuser


class ScientificPublicationDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'publications.delete_scientific_publication'

    def post(self, request, uuid):
        publicacion = get_object_or_404(ScientificPublication, uuid=uuid)
        log_action(
            user=self.request.user,
            obj=publicacion,
            action_flag=DELETION,
            message=f'Se eliminó la publicación científica: {publicacion.title}.',
        )
        try:
            publicacion.delete()
            messages.success(request, 'La publicación científica ha sido eliminada con éxito.')
        except Exception as e:
            messages.error(request, f'Error al eliminar la publicación científica: {str(e)}')
        return redirect('publications:list')


class ScientificPublicationFileDownloadView(ServeModelFileView):
    model = ScientificPublication
    field = 'pdf'
    permission_required = 'publications.view_scientific_publication'

    def get_filename(self, obj):
        fecha_str = obj.publication_date.strftime('%Y-%m-%d')
        return f'publicacion_{obj.title[:50]}_{fecha_str}.pdf'
