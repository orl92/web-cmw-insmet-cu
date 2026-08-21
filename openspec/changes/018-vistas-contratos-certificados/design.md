# 018 · Vistas de Certificados y Contratos — Plan

## Enfoque

Vistas CRUD siguiendo el patrón de otros modelos (ProvinceCRUD, StationCRUD). Mantener creación automática existente.

## Implementación

1. ContractListView, ContractCreateView, ContractDetailView, ContractDeleteView
2. CertificateListView, CertificateDetailView, CertificateDeleteView
3. Templates: listado, crear, detalle (extienden layouts/list.html y layouts/form.html)
4. URL patterns
5. Sidebar entries
6. No modificar InvoiceCreateView ni ApproveSubscriptionView
