# Identidad unificada

## Objetivo
Unificar columnas de identidad en cliente, reemplazar "Registro Comercial" por "Tipo de Cliente" en contratos, y hacer cumplir la regla identidad fiscal en el modelo Customer.

## Alcance por partes
### Parte 1 — Listado de clientes: una sola columna
- Unificar columnas "Identificación" y "Datos Fiscales" en una sola columna titulada "Identificación".
- Para persona jurídica: mostrar líneas etiquetadas REEUP y NIT (cada valor debajo de etiqueta), usando mismo estilo que antes para datos fiscales.
- Para persona natural: mostrar solo el número de carnet sin etiqueta, con estilo fw-medium font-monospace.
- El guion largo "—" solo aparece como último recurso cuando falta el dato que debería estar. Si una jurídica tiene REEUP pero falta NIT, mostrar REEUP y "—" para NIT.
- Actualizar tests afectados.

### Parte 2 — Listado de contratos: tipo de cliente en lugar de Registro Comercial
- Reemplazar columna "Registro Comercial" por "Tipo de Cliente" con badge (bg-green-lt para natural, bg-azure-lt para jurídica).
- Basado en object.customer.client_type; añadir select_related('customer__user') si necesario para evitar N+1.

### Parte 3 — El modelo hace cumplir la regla
- Añadir clean() en Customer: natural requiere identity_document; jurídica requiere company_name, reeup, nit.
- Reutilizar mensajes/constantes existentes donde sea limpio (sin romper formularios).
- Reutilizar validadores existentes (validate_reeup, validate_nit).
- Evaluar si llamar full_clean() en save() siguiendo patrón de Invoice.
- Añadir tests en apps/commercial/tests/test_models.py.
- Verificar que formulario POST inválido muestre un solo mensaje (evitar duplicación).

## Criterios de aceptación
- Columna unificada en listado de clientes según reglas.
- Columna "Tipo de Cliente" con badges en listado de contratos.
- Customer.clean() valida regla; tests nuevos pasan.
- Formularios existentes siguen pasando (sin duplicación indebida).
- Sin migraciones; sin cambios fuera de superficie permitida.

## Evidencia
- Título columna clientes: **Identificación** (unificada). Para natural solo carnet, para jurídica REEUP/NIT con etiquetas.
- Mensajes de validación: centralizados en `apps/commercial/models.py` (`CUSTOMER_*_ERROR`), `forms/customer.py` los importa para mantener los mismos textos.
- `Customer.save()` llama `self.full_clean()` por defecto (`run_validators=True`) siguiendo el patrón de `Invoice.save()`; se puede desactivar con `run_validators=False` para instancias que construyan datos parciales intencionalmente. El dato ajeno al tipo **no se prohíbe** explícitamente (la regla pedida es solo obligatoriedad).
- RED/GREEN: tests de clean nuevos pasan, listados actualizados OK.

## Comandos de verificación
- .venv/bin/python manage.py test apps.commercial
- .venv/bin/python manage.py check
- .venv/bin/ruff check apps/commercial
- .venv/bin/ruff format --check apps/commercial
- .venv/bin/djlint apps/commercial/templates/pages/commercial/customer/list.html apps/commercial/templates/pages/commercial/contract/list.html --lint
