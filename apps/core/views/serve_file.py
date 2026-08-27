from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.views import View


class ServeModelFileView(LoginRequiredMixin, View):
    """Sirve un FileField/ImageField de un modelo con Content-Disposition.

    Fuerza descarga (attachment) o previsualización (inline) según el query
    param ``?inline=1``, y define un nombre de archivo legible en lugar de
    depender del atributo ``download`` del navegador (que falla tras auth).
    """

    model = None
    field = 'pdf'  # FileField/ImageField name
    permission_required = None  # str o list[str] de codenames

    def get_queryset(self):
        return self.model._default_manager.all()

    def get_object(self):
        return get_object_or_404(self.get_queryset(), uuid=self.kwargs['uuid'])

    def get_filename(self, obj):
        raise NotImplementedError

    def get_permission_required(self, obj):
        return self.permission_required

    def get(self, request, uuid):
        obj = self.get_object()
        perm = self.get_permission_required(obj)
        if perm:
            perms = [perm] if isinstance(perm, str) else list(perm)
            if not any(request.user.has_perm(p) for p in perms):
                raise PermissionDenied
        f = getattr(obj, self.field)
        if not f:
            raise Http404
        disposition = 'inline' if request.GET.get('inline') else 'attachment'
        filename = self.get_filename(obj)
        response = FileResponse(f.open(), content_type='application/pdf')
        response['Content-Disposition'] = f'{disposition}; filename="{filename}"'
        return response
