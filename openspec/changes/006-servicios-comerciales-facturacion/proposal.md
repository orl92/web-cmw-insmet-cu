# 006 · Servicios comerciales y facturación

**Estado:** implementado ✅

## Qué hace

Gestión completa del ciclo comercial: clientes (con datos fiscales cubanos: REEUP, NIT, cuenta bancaria), servicios comerciales con precio en CUP, suscripciones con máquina de estados (requested → pending → paid → expired), soft delete, contratos con numeración automática (YYYY-NNNN), facturación con items y PDF descargable, cancelación suave de facturas, y certificados de suscripción.

## Por qué

El centro presta servicios meteorológicos comerciales a empresas. Se necesita un sistema que cubra desde la solicitud del cliente hasta la facturación y emisión de certificados, cumpliendo con requisitos fiscales cubanos.

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

## Fuera de alcance

- Pasarela de pago online.
- Facturación recurrente automática.
- Módulo de cobranzas.
