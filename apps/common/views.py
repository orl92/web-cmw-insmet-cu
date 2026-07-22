import csv

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponse
from django.views import View


def _resolve(value, obj):
    if callable(value):
        return value(obj)
    parts = value.split('__')
    current = obj
    for part in parts:
        current = getattr(current, part, '')
        if callable(current):
            current = current()
    return current if current is not None else ''


class CSVExportView(LoginRequiredMixin, PermissionRequiredMixin, View):
    model = None
    columns = []
    filename = 'export.csv'
    permission_required = None

    def get_queryset(self):
        return self.model.objects.all()

    def get_columns(self):
        return self.columns

    def get_filename(self):
        return self.filename

    def get(self, request):
        qs = self.get_queryset()
        columns = self.get_columns()
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="{self.get_filename()}"'
        response.write('\ufeff')
        writer = csv.writer(response)
        writer.writerow([h for h, _ in columns])
        for obj in qs:
            row = [_resolve(v, obj) for _, v in columns]
            writer.writerow(row)
        return response
