import base64
import os
from io import BytesIO

import xhtml2pdf.pisa as pisa
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import get_template
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DetailView, ListView, UpdateView, View

from common.utils import log_action
from dashboard.data.mail_send import mail_send
from dashboard.forms.tiempo.forms import WeatherReportForm
from dashboard.models import WeatherReport

REPORT_CONFIG = {
    'today': {
        'perm_prefix': 'weather_today',
        'segment': 'tiempo_h',
        'parent': 'tiempo',
        'title_create': 'Añadir Tiempo para Hoy',
        'title_list': 'Listado del Tiempo para Hoy',
        'title_update': 'Actualizar Tiempo para Hoy',
        'title_detail': 'Detalle Tiempo para Hoy',
        'btn': 'Añadir Tiempo para Hoy',
        'url_list': 'listado_tiempo_h',
        'url_create': 'crear_tiempo_h',
        'url_update': 'actualizar_tiempo_h',
        'url_delete': 'eliminar_tiempo_h',
        'url_detail': 'detalle_tiempo_h',
        'url_pdf': 'tiempo_h_pdf',
        'template_list': 'pages/dashboard/tiempo/hoy/listado_tiempo_h.html',
        'template_create': 'pages/dashboard/tiempo/hoy/crear_tiempo_h.html',
        'template_update': 'pages/dashboard/tiempo/hoy/actualizar_tiempo_h.html',
        'template_detail': 'pages/dashboard/tiempo/hoy/detalle_tiempo_h.html',
        'template_pdf': 'pages/dashboard/tiempo/hoy/pdf_template.html',
        'subject_create': 'El Tiempo para Hoy',
        'subject_update': 'El Tiempo para Hoy Actualizado',
        'pdf_filename_prefix': 'tiempo_hoy',
        'context_name': 'weather_today',
        'mail_url': 'tiempo_h',
    },
    'tomorrow': {
        'perm_prefix': 'weather_tomorrow',
        'segment': 'tiempo_m',
        'parent': 'tiempo',
        'title_create': 'Añadir Tiempo para Mañana',
        'title_list': 'Listado del Tiempo para Mañana',
        'title_update': 'Actualizar Tiempo para Mañana',
        'title_detail': 'Detalle Tiempo para Mañana',
        'btn': 'Añadir Tiempo para Mañana',
        'url_list': 'listado_tiempo_m',
        'url_create': 'crear_tiempo_m',
        'url_update': 'actualizar_tiempo_m',
        'url_delete': 'eliminar_tiempo_m',
        'url_detail': 'detalle_tiempo_m',
        'url_pdf': 'tiempo_m_pdf',
        'template_list': 'pages/dashboard/tiempo/manana/listado_tiempo_m.html',
        'template_create': 'pages/dashboard/tiempo/manana/crear_tiempo_m.html',
        'template_update': 'pages/dashboard/tiempo/manana/actualizar_tiempo_m.html',
        'template_detail': 'pages/dashboard/tiempo/manana/detalle_tiempo_m.html',
        'template_pdf': 'pages/dashboard/tiempo/manana/pdf_template.html',
        'subject_create': 'El Tiempo para Mañana',
        'subject_update': 'El Tiempo para Mañana Actualizado',
        'pdf_filename_prefix': 'tiempo_manana',
        'context_name': 'weather_tomorrow',
        'mail_url': 'tiempo_m',
    },
    'commentary': {
        'perm_prefix': 'weather_commentary',
        'segment': 'comentario_tiempo',
        'parent': 'comentario',
        'title_create': 'Añadir Comentario del Tiempo',
        'title_list': 'Listado de Comentarios del Tiempo',
        'title_update': 'Actualizar Comentario del Tiempo',
        'title_detail': 'Detalle Comentario del Tiempo',
        'btn': 'Añadir Comentario del Tiempo',
        'url_list': 'listado_comentarios_tiempo',
        'url_create': 'crear_comentario_tiempo',
        'url_update': 'actualizar_comentario_tiempo',
        'url_delete': 'eliminar_comentario_tiempo',
        'url_detail': 'detalle_comentario_tiempo',
        'url_pdf': 'comentario_tiempo_pdf',
        'template_list': 'pages/dashboard/comentarios/tiempo/listado_comentarios_tiempo.html',
        'template_create': 'pages/dashboard/comentarios/tiempo/crear_comentario_tiempo.html',
        'template_update': 'pages/dashboard/comentarios/tiempo/actualizar_comentario_tiempo.html',
        'template_detail': 'pages/dashboard/comentarios/tiempo/detalle_comentario_tiempo.html',
        'template_pdf': 'pages/dashboard/comentarios/tiempo/pdf_template.html',
        'subject_create': 'Comentario del Tiempo',
        'subject_update': 'Comentario del Tiempo Actualizado',
        'pdf_filename_prefix': 'comentario_tiempo',
        'context_name': 'weather_commentary',
        'mail_url': 'comentario_tiempo',
    },
    'note': {
        'perm_prefix': 'weather_note',
        'segment': 'nota_meteorologica',
        'parent': 'comentario',
        'title_create': 'Añadir Nota Meteorológica',
        'title_list': 'Listado de Notas Meteorológicas',
        'title_update': 'Actualizar Nota Meteorológica',
        'title_detail': 'Detalle Nota Meteorológica',
        'btn': 'Añadir Nota Meteorológica',
        'url_list': 'listado_notas_meteorologicas',
        'url_create': 'crear_nota_meteorologica',
        'url_update': 'actualizar_nota_meteorologica',
        'url_delete': 'eliminar_nota_meteorologica',
        'url_detail': 'detalle_nota_meteorologica',
        'url_pdf': 'nota_meteorologica_pdf',
        'template_list': 'pages/dashboard/comentarios/nota_meteorologica/listado_notas_meteorologicas.html',
        'template_create': 'pages/dashboard/comentarios/nota_meteorologica/crear_nota_meteorologica.html',
        'template_update': 'pages/dashboard/comentarios/nota_meteorologica/actualizar_nota_meteorologica.html',
        'template_detail': 'pages/dashboard/comentarios/nota_meteorologica/detalle_nota_meteorologica.html',
        'template_pdf': 'pages/dashboard/comentarios/nota_meteorologica/pdf_template.html',
        'subject_create': 'Nota Meteorológica',
        'subject_update': 'Nota Meteorológica Actualizada',
        'pdf_filename_prefix': 'nota_meteorologica',
        'context_name': 'weather_note',
        'mail_url': 'nota_meteorologica',
    },
}


class WeatherReportListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = WeatherReport

    def get_report_type(self):
        return self.kwargs.get('report_type', 'today')

    def get_config(self):
        return REPORT_CONFIG[self.get_report_type()]

    @property
    def permission_required(self):
        cfg = self.get_config()
        return f'dashboard.view_{cfg["perm_prefix"]}'

    def get_template_names(self):
        return [self.get_config()['template_list']]

    def get_queryset(self):
        return WeatherReport.objects.filter(type=self.get_report_type())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cfg = self.get_config()
        context['title'] = cfg['title_list']
        context['parent'] = cfg['parent']
        context['segment'] = cfg['segment']
        context['btn'] = cfg['btn']
        context['url_create'] = reverse_lazy(cfg['url_create'])
        context['url_list'] = reverse_lazy(cfg['url_list'])
        context['is_staff'] = self.request.user.is_staff or self.request.user.is_superuser
        context['is_superuser'] = self.request.user.is_superuser
        context['url_export'] = reverse_lazy('exportar_csv_tiempo')
        context['objects'] = self.get_queryset()
        return context


class WeatherReportCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = WeatherReport
    form_class = WeatherReportForm

    def get_report_type(self):
        return self.kwargs.get('report_type', 'today')

    def get_config(self):
        return REPORT_CONFIG[self.get_report_type()]

    @property
    def permission_required(self):
        cfg = self.get_config()
        return f'dashboard.add_{cfg["perm_prefix"]}'

    def get_template_names(self):
        return [self.get_config()['template_create']]

    def get_success_url(self):
        return reverse_lazy(self.get_config()['url_list'])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['report_type'] = self.get_report_type()
        return kwargs

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.date = timezone.now()
        instance.save()
        response = super().form_valid(form)
        cfg = self.get_config()

        log_action(
            user=self.request.user,
            obj=self.object,
            action_flag=ADDITION,
            message=f"Se creó un nuevo {cfg['title_create']}: {self.object.date}."
        )

        messages.success(self.request, f'{cfg["title_create"]} ha sido creado con éxito.', extra_tags='success')
        mail_send(self.request, self.object, cfg['subject_create'], cfg['mail_url'])

        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cfg = self.get_config()
        context['title'] = cfg['title_create']
        context['parent'] = cfg['parent']
        context['segment'] = cfg['segment']
        context['url_list'] = reverse_lazy(cfg['url_list'])
        return context


class WeatherReportUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin, UpdateView):
    model = WeatherReport
    form_class = WeatherReportForm

    def get_report_type(self):
        return self.kwargs.get('report_type', 'today')

    def get_config(self):
        return REPORT_CONFIG[self.get_report_type()]

    @property
    def permission_required(self):
        cfg = self.get_config()
        return f'dashboard.change_{cfg["perm_prefix"]}'

    def get_template_names(self):
        return [self.get_config()['template_update']]

    def get_success_url(self):
        return reverse_lazy(self.get_config()['url_list'])

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(WeatherReport, uuid=uuid)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['report_type'] = self.get_report_type()
        return kwargs

    def form_valid(self, form):
        original_object = self.get_object(queryset=None)
        relevant_fields = ['summary', 'file', 'email_recipient_list']
        has_changes = any(
            form.cleaned_data[field] != getattr(original_object, field)
            for field in relevant_fields
        )
        cfg = self.get_config()

        instance = form.save(commit=False)
        instance.date = timezone.now()
        instance.save()
        response = super().form_valid(form)

        log_action(
            user=self.request.user,
            obj=self.object,
            action_flag=CHANGE,
            message=f"Se actualizó {cfg['title_update']}: {self.object.date}."
        )

        if has_changes:
            mail_send(self.request, self.object, cfg['subject_update'], cfg['mail_url'])

        messages.success(self.request, f'{cfg["title_update"]} ha sido actualizado con éxito.', extra_tags='success')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cfg = self.get_config()
        context['title'] = cfg['title_update']
        context['parent'] = cfg['parent']
        context['segment'] = cfg['segment']
        context['url_list'] = reverse_lazy(cfg['url_list'])
        return context

    def test_func(self):
        return self.request.user.is_superuser or self.get_object().user == self.request.user


class WeatherReportDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    def get_report_type(self):
        return self.kwargs.get('report_type', 'today')

    def get_config(self):
        return REPORT_CONFIG[self.get_report_type()]

    @property
    def permission_required(self):
        cfg = self.get_config()
        return f'dashboard.delete_{cfg["perm_prefix"]}'

    def post(self, request, uuid, *args, **kwargs):
        obj = get_object_or_404(WeatherReport, uuid=uuid)
        cfg = self.get_config()
        log_action(
            user=self.request.user,
            obj=obj,
            action_flag=DELETION,
            message=f"Se eliminó {cfg['title_list']}: {obj.date.strftime('%d-%m-%Y')}."
        )
        try:
            obj.delete()
            messages.success(request, f'{cfg["title_list"]} ha sido eliminado con éxito.')
        except Exception as e:
            messages.error(request, str(e))
        return redirect(cfg['url_list'])


class WeatherReportDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = WeatherReport

    def get_report_type(self):
        return self.kwargs.get('report_type', 'today')

    def get_config(self):
        return REPORT_CONFIG[self.get_report_type()]

    @property
    def permission_required(self):
        cfg = self.get_config()
        return f'dashboard.view_{cfg["perm_prefix"]}'

    def get_template_names(self):
        return [self.get_config()['template_detail']]

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(WeatherReport, uuid=uuid)

    def get_context_object_name(self, obj):
        return self.get_config()['context_name']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cfg = self.get_config()
        context['title'] = cfg['title_detail']
        context['parent'] = cfg['parent']
        context['segment'] = cfg['segment']
        context['url_list'] = reverse_lazy(cfg['url_list'])
        return context


class WeatherReportPDFView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = WeatherReport

    def get_report_type(self):
        return self.kwargs.get('report_type', 'today')

    def get_config(self):
        return REPORT_CONFIG[self.get_report_type()]

    @property
    def permission_required(self):
        cfg = self.get_config()
        return f'dashboard.view_{cfg["perm_prefix"]}'

    def get_object(self, queryset=None):
        uuid = self.kwargs.get('uuid')
        return get_object_or_404(WeatherReport, uuid=uuid)

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        cfg = self.get_config()

        logo_path = os.path.join(settings.BASE_DIR, "static/dist/img/logo.png")
        logo_base64 = self.get_image_base64(logo_path)

        template = get_template(cfg['template_pdf'])
        context = {cfg['context_name']: obj, 'logo_base64': logo_base64}
        html = template.render(context)

        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)

        if not pdf.err:
            response = HttpResponse(result.getvalue(), content_type='application/pdf')
            filename = f"{cfg['pdf_filename_prefix']}_{obj.date.strftime('%Y-%m-%d')}.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        return HttpResponse("Error al generar el PDF", status=400)

    @staticmethod
    def get_image_base64(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
