# 072 — dark-mode

## Motivación

Tabler soporta dark mode nativamente con clase `.dark` en `<html>`. El proyecto incluye el toggle en la interfaz pero la elección no persiste entre páginas ni sesiones.

## Alcance

- Persistencia vía `localStorage` (clave `tablerTheme`)
- Sincronizar con el toggle existente en `base.html`
- Aplicar tema al cargar página antes de paint (script inline en `<head>`)

## Criterios de Aceptación

1. Toggle cambia clase `.dark` en `<html>` y guarda en localStorage
2. Al recargar, el tema persiste (sin flicker)
3. Coherente en todas las páginas (usa misma lógica en base-auth.html si aplica)
