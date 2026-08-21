# Spec — 006-servicios-comerciales-facturacion

## Criterios de aceptación

- [x] Clientes con datos fiscales validados (REEUP formato `###.#.####`, NIT 11 dígitos, cuenta 16 dígitos).
- [x] Servicios comerciales con código único, precio, imagen.
- [x] Suscripciones con estados: requested → pending → paid → expired.
- [x] Soft delete de suscripciones (`record_active=False`).
- [x] Contratos con número auto-generado `YYYY-NNNN`.
- [x] Facturas con items, cálculo automático de importe, PDF (pdfkit).
- [x] Cancelación suave de facturas (`is_cancelled=True`).
- [x] Certificados de suscripción (subidos por admin, enviados por correo).
- [x] Dashboard CRUD para clientes, servicios, suscripciones, facturas.
- [x] Vistas públicas para listar y solicitar servicios comerciales.
