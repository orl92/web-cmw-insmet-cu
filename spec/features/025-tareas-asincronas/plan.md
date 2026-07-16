# 025 · Tareas asíncronas — Plan

## Enfoque

Usar Huey (más simple que Celery, soporta SQLite como broker). No requiere Redis.

## Implementación

1. Agregar `huey` a requirements.txt
2. Configurar Huey en settings.py (usar SQLite como broker para dev)
3. Crear `dashboard/tasks.py` con tareas
4. Reemplazar `mail_send()` por task
5. Reemplazar PDF generation en facturación por task
6. Tests básicos
