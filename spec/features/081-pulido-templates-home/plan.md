# 081 — plan

## Objetivo
Limpiar HTML inválido, redundancias y problemas de jerarquía de encabezados en las templates públicas del home, sin cambiar comportamiento ni contenido.

## Decisiones previas
- Los cambios son puramente de template; no requieren migraciones ni tocar modelos/vistas.
- La verificación visual se hace con render por test client (200) + inspección manual, ya que no hay tests de templates del home.

## Orden de trabajo
1. Establecer estado base: confirmar render actual de `home:index` (test client, 200).
2. Footer: unificar bandas, limpiar `rel` y `document.write`.
3. Navbar: quitar wrapper anidado, borrar bloque comentado, cambiar brand a no-heading.
4. Investigar 7 (forecast_region_card) y 8 (empty_state) y corregir o descartar.
5. Verificación final (see tasks).