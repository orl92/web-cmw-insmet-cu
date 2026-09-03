import re
from urllib.parse import quote

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.views import View


def _ascii_filename(name):
    """ASCII-safe fallback for the Content-Disposition ``filename`` param.

    Non-ASCII bytes or raw spaces in ``filename="..."`` can make some
    browsers ignore the whole header and fall back to inline (opening the
    PDF instead of downloading). The real Unicode name travels in
    ``filename*`` (RFC 5987); this keeps the primary param valid ASCII.
    """
    return re.sub(r'[^A-Za-z0-9_.-]', '_', name)


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
        ascii_name = _ascii_filename(filename)
        encoded = quote(filename)
        response['Content-Disposition'] = (
            f'{disposition}; filename="{ascii_name}"; filename*=UTF-8\'\'{encoded}'
        )
        # The PDF modal embeds this file in an <object> (Firefox treats it as
        # a frame). The global X-Frame-Options: DENY would block that, so allow
        # same-origin framing only for the inline preview. Attachment stays DENY.
        if disposition == 'inline':
            response['X-Frame-Options'] = 'SAMEORIGIN'
        return response


class PublicServeFileView(View):
    """Sirve un FileField de un modelo accesible sin autenticación.

    Usado por el portal público (home) para incrustar los PDFs que la página
    ya muestra (reportes del tiempo, publicaciones científicas). Replica el
    contrato de ``ServeModelFileView`` — ``?inline=1`` fuerza
    ``Content-Disposition: inline`` + ``X-Frame-Options: SAMEORIGIN`` para que
    el modal PDF (``<object>``) embeba el documento same-origin — pero sin
    ``LoginRequiredMixin`` ni permisos. El ``field`` apunta al FileField y
    ``get_queryset`` puede restringir en qué registros se permite servir.
    """

    model = None
    field = 'file'

    def get_queryset(self):
        return self.model._default_manager.all()

    def get_object(self):
        return get_object_or_404(self.get_queryset(), uuid=self.kwargs['uuid'])

    def get_filename(self, obj):
        return getattr(obj, self.field).name.rsplit('/', 1)[-1]

    def get(self, request, uuid):
        obj = self.get_object()
        f = getattr(obj, self.field)
        if not f:
            raise Http404
        disposition = 'inline' if request.GET.get('inline') else 'attachment'
        filename = self.get_filename(obj)
        response = FileResponse(f.open(), content_type='application/pdf')
        ascii_name = _ascii_filename(filename)
        encoded = quote(filename)
        response['Content-Disposition'] = (
            f'{disposition}; filename="{ascii_name}"; filename*=UTF-8\'\'{encoded}'
        )
        if disposition == 'inline':
            response['X-Frame-Options'] = 'SAMEORIGIN'
        return response
