# 070 — tests-secundarios

## Motivación

`apps/dashboard/`, `apps/core/` (middleware) y las tareas Huey en `apps/core/tasks.py` tienen cobertura insuficiente o nula.

## Alcance

- Dashboard: tests para `DashboardView` (charts, KPIs, queries optimizadas)
- Middleware: `CheckUserProfileMiddleware`, `MaintenanceModeMiddleware`
- Huey tasks genéricas: `send_email_task`

## Criterios de Aceptación

1. `DashboardView` testea context con KPIs, charts data, filtering por grupo staff
2. Maintenance mode bloquea no-superusers excepto `/login/`
3. `CheckUserProfileMiddleware` redirige a completar perfil si falta
4. `send_email_task` envía correo con adjuntos
5. `python manage.py test` pasa
