# Tasks — 069 tests-comerciales

## Fase 1: test_models.py

- [x] `__init__.py` creado
- [ ] Customer: creación, str (natural/jurídica), UUID, permisos, soft delete, hard delete, unique constraints
- [ ] Service: creación, str, UUID, permisos, soft delete, hard delete, FileHandlerMixin, `get_image_url()`
- [ ] ServiceSubscription: creación, str, UUID, permisos, soft delete, `clean()` date validation, `is_active`, `status_display`
- [ ] Invoice: creación, str, UUID, permisos, soft delete, `clean()` amount validation
- [ ] InvoiceItem: creación, str, UUID, permisos, `save()` computa importe, `clean()` cantidad/precio validation
- [ ] Contract: creación, str, UUID, permisos, soft delete
- [ ] Certificate: creación, str, UUID, permisos, soft delete, FileHandlerMixin

## Fase 2: test_forms.py

- [ ] CustomerForm: password2 mismatch, conditional required (jurídica), regex fields, uniqueness, save() creates User
- [ ] CustomerUpdateForm: regex, uniqueness exclude self, email update
- [ ] CustomerForUserForm: regex, uniqueness (new vs existing), user assignment
- [ ] ServiceForm: PUBLIC requires pdf, rejects image; COMMERCIAL requires code/price/image, rejects pdf
- [ ] SubscriptionForm: period calculation (1m/3m/6m/1y), custom date validation
- [ ] CertificateUploadForm, PaymentMethodForm, InvoiceForm, ContractForm, CertificateForm: básicos

## Fase 3: test_views.py

- [ ] Customer: list, create, update (owner vs superuser), delete (soft), hard_delete (superuser)
- [ ] Service: list, create, update, delete, hard_delete
- [ ] Subscription: list, create, update, cancel, renew, approve (flujo completo)
- [ ] Invoice: list, create, cancel
- [ ] Contract: list, create, detail, delete
- [ ] Certificate: list, create, detail, pdf, delete
- [ ] CSV exports: todas las 6 vistas
- [ ] RegenerateInvoice, ResendCertificateEmail, ResendInvoiceEmail

## Fase 4: test_tasks.py

- [ ] `generate_invoice_pdf_and_email_task`: genera PDF, envía email, actualiza flags
- [ ] `send_email_task`: envía correo con adjuntos
