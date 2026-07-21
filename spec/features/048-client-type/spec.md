# 048 — Soporte para Persona Natural en Customer

## Qué hace

Permite que una persona natural (no empresa) se registre como cliente sin necesidad de REEUP, NIT ni razón social.

## Criterios de aceptación

- [ ] El modelo `Customer` tiene un campo `client_type` con opciones `natural` / `juridica` (default `juridica`)
- [ ] `company_name`, `reeup`, `nit` son opcionales (null=True, blank=True)
- [ ] El formulario de registro público (`CustomerSignUpForm`) permite elegir tipo de cliente al inicio del paso 3
- [ ] Si `client_type = natural`: se ocultan REEUP, NIT, company_name; se muestra solo nombre completo, dirección, teléfono
- [ ] Si `client_type = juridica`: se muestran todos los campos como antes
- [ ] Los formularios de dashboard (`CustomerForm`, `CustomerUpdateForm`) también soportan ambos tipos con validación condicional
- [ ] El `__str__` de Customer usa `company_name` si existe, o `user.get_full_name()` si es persona natural
- [ ] Migraciones creadas y aplicadas sin errores
- [ ] `python manage.py check` sin errores
- [ ] Tests existentes siguen pasando
