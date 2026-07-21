# 030 — Mejoras al workflow de desarrollo

## Qué hace

Refina AGENTS.md con:
1. Documentación robusta de cómo mantener el worker Huey corriendo (nohup, tmux, Supervisor).
2. Política de testing selectivo: solo correr tests que afectan al código modificado.
3. Política de creación de tests: si no existe test para el cambio, crearlo.
4. Verificación de seguridad explícita post-cambio.

## Criterios de aceptación

- AGENTS.md incluye una subsección "Worker de correos (Huey)" con 3 métodos documentados.
- La sección Testing especifica el comando `python manage.py test <app>` en vez del test completo.
- El paso 7 de SSD referencia verificación selectiva + seguridad.
- Nuevo checklist "Seguridad post-cambio" en la sección de revisión.
- `python manage.py check` no reporta errores.
