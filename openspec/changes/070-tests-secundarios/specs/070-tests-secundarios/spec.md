# Spec — 070-tests-secundarios

## Criterios de Aceptación

1. `DashboardView` testea context con KPIs, charts data, filtering por grupo staff
2. Maintenance mode bloquea no-superusers excepto `/login/`
3. `CheckUserProfileMiddleware` redirige a completar perfil si falta
4. `send_email_task` envía correo con adjuntos
5. `python manage.py test` pasa
