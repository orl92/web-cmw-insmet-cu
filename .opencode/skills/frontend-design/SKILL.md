---
name: frontend-design
description: "Trigger: frontend, diseño visual, UI, identidad, Tabler, componentes. Diseño visual con identidad para vistas y componentes del proyecto."
license: Apache-2.0
metadata:
  author: "yoelvismr"
  version: "1.0"
---

# Skill: frontend-design

## Activation Contract

Cargar al crear o rediseñar vistas, componentes, layouts o cualquier UI del proyecto.

## Hard Rules

- UI exclusivamente con Tabler.io (Bootstrap 5). Prohibido otros frameworks CSS/UI.
- Templates Django con indentación de 2 espacios, formateados con djlint.
- Templates de correo en `*/emails/` NO se reindentan (whitespace-sensitive).
- Iconos meteorológicos: PNGs en `static/dist/img/weather_icon/`.
- Textos de UI en español, registro neutral/profesional.
- Idioma/región del sitio: `es-mx`, `America/Havana`.

## Decision Gates

| Necesidad | Recurso |
|---|---|
| Icono/componente Tabler | Buscar en la documentación Tabler antes de inventar |
| Gráfico meteorológico | Generadores en `apps/home/data/plot_generators.py` |
| Página pública | Plantillas en `templates/` con `layouts/` e `includes/` |

## Execution Steps

1. Identificar el layout base y componentes Tabler ya usados en el proyecto.
2. Diseñar con identidad consistente (paleta, tipografía, espaciado del tema actual).
3. Escribir el template Django con 2 espacios.
4. Verificar: `djlint . --reformat --check` y `djlint . --lint` sobre los templates tocados.

## Output Contract

- Template(s) Django con indentación djlint-compatible.
- Cambios coherentes con la identidad visual existente.
- Resultado de la verificación djlint.

## References

- `../../AGENTS.md` — convenciones UI, estáticos y templates.
- `../../../templates/` — layouts e includes existentes.
