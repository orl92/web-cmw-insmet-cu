# Plan — 035-migrar-is-staff

## Enfoque técnico
1. En `list.html:4`: cambiar `{% if is_staff %}` a `{% if request.user.is_staff %}`
2. En las 21 vistas: eliminar `context['is_staff'] = self.request.user.is_staff or self.request.user.is_superuser`
3. Verificar que ninguna vista externa usa la variable is_staff en su template

## App(s) modificada(s)
- accounts/views/user/, accounts/views/group/
- dashboard/views/comentarios/, certificados/, clientes/, contratos/,
  email_recipient/, estaciones/, facturacion/, municipios/, provincias/,
  pronosticos/, publicaciones/, servicios/, suscripciones/, tiempo/,
  avisos/*/
- templates/layouts/list.html
