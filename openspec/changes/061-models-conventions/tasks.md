# Tasks — 061-models-conventions

## FileHandlerMixin

- [ ] `apps/dashboard/models.py:667` — Agregar `FileHandlerMixin` a la
      herencia de `Invoice`: `(SoftDeleteModel, FileHandlerMixin, models.Model)`
- [ ] `apps/dashboard/models.py:690` — Agregar `file_fields = ['pdf']` en
      `Invoice`
- [ ] `apps/dashboard/models.py:747` — Agregar `FileHandlerMixin` a la
      herencia de `Certificate`: `(SoftDeleteModel, FileHandlerMixin, models.Model)`
- [ ] `apps/dashboard/models.py:770` — Agregar `file_fields = ['pdf']` en
      `Certificate`

## Meta.ordering

- [ ] `apps/dashboard/models.py:735-744` — Agregar `ordering = ['invoice', 'codigo']`
      en `InvoiceItem.Meta`
- [ ] `apps/dashboard/models.py:796-818` — Agregar `ordering = ['-date']`
      en `WeatherReport.Meta`
- [ ] `apps/dashboard/models.py:408-417` — Agregar `ordering = ['-date']`
      en `EarlyWarning.Meta`
- [ ] `apps/dashboard/models.py:421-430` — Agregar `ordering = ['-date']`
      en `TropicalCyclone.Meta`
- [ ] `apps/dashboard/models.py:434-443` — Agregar `ordering = ['-date']`
      en `StormWarning.Meta`

## related_name

- [ ] `apps/dashboard/models.py:391` — Agregar `related_name="%(class)s_warnings"`
      a `BaseWarning.user`
- [ ] `apps/dashboard/models.py:716` — Agregar `related_name="invoice_items"`
      a `InvoiceItem.subscription`

## SiteConfiguration cleanup

- [ ] `apps/dashboard/models.py:20` — Eliminar `id = models.AutoField(primary_key=True)`
- [ ] Buscar referencias a `siteconfiguration.id` en views/templates y migrar a `uuid`

## Verificación

- [ ] `python manage.py makemigrations && python manage.py migrate`
- [ ] `python manage.py test`
- [ ] `python manage.py check`
