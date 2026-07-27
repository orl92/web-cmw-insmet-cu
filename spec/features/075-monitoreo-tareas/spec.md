# 075 — monitoreo-tareas

## Motivación

Huey procesa tareas críticas (generación de PDF, envío de correos) pero no hay visibilidad del estado de las tareas. Si un worker falla o una tarea se encola, no hay forma de detectarlo hasta que un usuario reporta que no recibió su factura.

## Alcance

- Agregar `huey.contrib.djhuey` y registrar modelos de tareas en admin
- O crear vista simple de monitoreo accesible a superusers
- Mostrar: cola pendiente, tareas fallidas, reintentos, tiempo de ejecución

## Criterios de Aceptación

1. Superuser puede ver estado de tareas Huey desde el dashboard
2. Tareas fallidas son visibles con traceback
3. Alerta visual si hay tareas en cola por más de 5 min
