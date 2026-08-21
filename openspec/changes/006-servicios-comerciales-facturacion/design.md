# 006 · Servicios comerciales y facturación — Plan

## Enfoque

6 modelos (Customer, Service, ServiceSubscription, Contract, Invoice, InvoiceItem, Certificate) con relaciones cuidadosas. Máquina de estados en ServiceSubscription. PDF de factura con pdfkit. Soft delete para suscripciones y cancelación suave para facturas.

## Implementación

1. **Modelos**: Customer (OneToOne→User), Service (reutilizado de feature 005, `service_type='commercial'`), ServiceSubscription (FK→Customer, FK→Service, estados, soft delete), Contract (OneToOne→Subscription), Invoice (FK→Subscription/Customer, PDF, is_cancelled), InvoiceItem (FK→Invoice), Certificate (FK→Subscription, PDF).
2. **Dashboard**: CRUDs para cada modelo; `ApproveSubscriptionView` para subir certificado y cambiar estado a paid; `CancelInvoiceView` para `is_cancelled=True`; `SubscriptionRenewView` para renovar.
3. **Público**: `CommercialServicesListView` (suscripciones activas del usuario logueado), `PublicCommercialServicesListView` (listado general), `ServiceDetailView` (detalle + formulario de solicitud).
4. **PDF**: `InvoiceCreateView.generate_pdf()` con pdfkit renderiza `factura_template.html` → A4.

## Decisiones

- **Soft delete vs hard delete** — suscripciones usan `record_active` para conservar historial; facturas usan `is_cancelled` para mantener integridad contable.
- **Numeración `YYYY-NNNN`** — reinicia cada año, secuencia por año fiscal cubano.
- **pdfkit en vez de xhtml2pdf** — mejor soporte CSS para facturas A4; requiere wkhtmltopdf en el servidor.
- **Singletons**: `CompanySettings` (pk=1) para datos fiscales de la empresa que aparecen en facturas.

## Riesgos

- **wkhtmltopdf requerido** — `pdfkit` depende de wkhtmltopdf; si no está instalado, la generación de facturas falla. Se documenta en setup.
- **Integridad de estados** — cambios de estado no validados pueden dejar suscripciones en estado inconsistente; se controla desde las vistas.
