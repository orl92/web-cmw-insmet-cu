from django.contrib import messages
from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UserPassesTestMixin)
from django.contrib.auth.models import Group, Permission
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView, View

from apps.accounts.forms.group.form import GroupForm
from apps.accounts.models import GroupProfile
from apps.common.utils import log_action

# Create your views here.


class GroupListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    template_name = "pages/accounts/groups/groups.html"
    permission_required = "auth.view_group"
    model = Group

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Listado de Grupos"
        context["parent"] = "accounts"
        context["segment"] = "groups"
        context["btn"] = "Añadir Grupo"
        context["url_create"] = reverse_lazy("accounts:group_create")
        context["url_list"] = reverse_lazy("accounts:groups_list")
        context['is_superuser'] = self.request.user.is_superuser
        context["objects"] = Group.objects.all()
        return context


class GroupCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Group
    form_class = GroupForm
    template_name = "pages/accounts/groups/group_create.html"
    permission_required = "auth.add_group"
    success_url = reverse_lazy("accounts:groups_list")
    url_redirect = success_url

    def form_valid(self, form):
        group = form.save()
        group_profile, created = GroupProfile.objects.get_or_create(group=group)

        # Registro de acción
        log_action(
            user=self.request.user,
            obj=group,
            action_flag=ADDITION,
            message=f"Se creó un nuevo grupo {group.name}.")

        messages.success(
            self.request, "El grupo ha sido creado con éxito.", extra_tags="success"
        )
        return redirect("accounts:groups_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Añadir Grupo"
        context["parent"] = "accounts"
        context["segment"] = "groups"
        context["url_list"] = self.success_url

        # Obtener todos los permisos de dashboard
        from django.db.models import Q

        permissions = Permission.objects.filter(
            Q(content_type__app_label="dashboard")
        ).select_related("content_type")

        # Preparar datos para la tabla
        grouped_permissions = {}

        for perm in permissions:
            # Obtener el nombre del modelo (verbose_name)
            try:
                model_class = perm.content_type.model_class()
                if model_class:
                    model_name = model_class._meta.verbose_name
                else:
                    model_name = perm.content_type.model.replace("_", " ").title()
            except:  # noqa: E722
                model_name = perm.content_type.model.replace("_", " ").title()

            # Determinar tipo de permiso
            codename = perm.codename.lower()
            if codename.startswith("view_"):
                perm_type = "view"
            elif codename.startswith("add_"):
                perm_type = "add"
            elif codename.startswith("change_"):
                perm_type = "change"
            elif codename.startswith("delete_"):
                perm_type = "delete"
            else:
                continue  # Saltar permisos que no sean CRUD

            # Inicializar el modelo si no existe
            if model_name not in grouped_permissions:
                grouped_permissions[model_name] = {
                    "view": None,
                    "add": None,
                    "change": None,
                    "delete": None,
                }

            # Asignar el permiso
            grouped_permissions[model_name][perm_type] = {
                "perm": perm,
                "field_name": "permissions",
                "field_id": f"perm_{perm.id}",
                "is_checked": False,  # Por defecto en creación
            }

        # Ordenar por nombre del modelo
        context["grouped_permissions"] = dict(sorted(grouped_permissions.items()))

        return context


class GroupUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Group
    form_class = GroupForm
    template_name = "pages/accounts/groups/group_update.html"
    permission_required = "auth.change_group"
    success_url = reverse_lazy("accounts:groups_list")

    def get_object(self):
        uuid = self.kwargs.get("uuid")
        group_profile = get_object_or_404(GroupProfile, uuid=uuid)
        return group_profile.group

    def form_valid(self, form):
        response = super().form_valid(form)

        # Registro de acción
        log_action(
            user=self.request.user,
            obj=self.object,
            action_flag=CHANGE,
            message=f"Se actualizó el grupo {self.object.name}.")

        messages.success(
            self.request,
            "El grupo ha sido actualizado con éxito.",
            extra_tags="warning")
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Actualizar Grupo"
        context["parent"] = "accounts"
        context["segment"] = "groups"
        context["url_list"] = self.success_url

        group = self.get_object()
        group_permissions = group.permissions.all()

        # Obtener todos los permisos disponibles
        from django.db.models import Q

        permissions = Permission.objects.filter(
            Q(content_type__app_label="dashboard")
        ).select_related("content_type")

        # Preparar datos para la tabla
        grouped_permissions = {}

        for perm in permissions:
            # Obtener el nombre del modelo (verbose_name)
            try:
                model_class = perm.content_type.model_class()
                if model_class:
                    model_name = model_class._meta.verbose_name
                else:
                    model_name = perm.content_type.model.replace("_", " ").title()
            except:  # noqa: E722
                model_name = perm.content_type.model.replace("_", " ").title()

            # Determinar tipo de permiso
            codename = perm.codename.lower()
            if codename.startswith("view_"):
                perm_type = "view"
            elif codename.startswith("add_"):
                perm_type = "add"
            elif codename.startswith("change_"):
                perm_type = "change"
            elif codename.startswith("delete_"):
                perm_type = "delete"
            else:
                continue  # Saltar permisos que no sean CRUD

            # Inicializar el modelo si no existe
            if model_name not in grouped_permissions:
                grouped_permissions[model_name] = {
                    "view": None,
                    "add": None,
                    "change": None,
                    "delete": None,
                }

            # Verificar si el permiso está en el grupo
            is_checked = perm in group_permissions

            # Asignar el permiso
            grouped_permissions[model_name][perm_type] = {
                "perm": perm,
                "field_name": "permissions",
                "field_id": f"perm_{perm.id}",
                "is_checked": is_checked,
            }

        # Ordenar por nombre del modelo
        context["grouped_permissions"] = dict(sorted(grouped_permissions.items()))

        return context

    def test_func(self):
        return self.request.user.is_superuser


class GroupDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'auth.delete_group'

    def post(self, request, uuid):
        groupprofile = get_object_or_404(GroupProfile, uuid=uuid)
        group = groupprofile.group
        log_action(
            user=self.request.user,
            obj=group,
            action_flag=DELETION,
            message=f"Se eliminó al grupo {group.name}."
        )
        try:
            group.delete()
            messages.success(request, f'Grupo {group.name} eliminado correctamente.')
        except Exception as e:
            messages.error(request, str(e))
        return redirect('accounts:groups_list')
