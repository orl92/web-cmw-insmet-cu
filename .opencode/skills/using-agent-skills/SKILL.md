---
name: using-agent-skills
description: "Trigger: qué skill usar, elegir skill, skill para esta tarea, cuál skill. Árbol de decisión para seleccionar la skill correcta según la tarea."
license: Apache-2.0
metadata:
  author: "yoelvismr"
  version: "1.0"
---

# Skill: using-agent-skills

## Activation Contract

Cargar al inicio de una tarea cuando haya dudas sobre qué skill aplicar, o cuando el usuario pregunte qué skills existen.

## Hard Rules

- La lista `<available_skills>` del sistema es autoritativa; si una skill no aparece, no está disponible.
- Skills de proyecto viven en `.opencode/skills/`; globales en `~/.config/opencode/skills/`.
- Cargar la skill ANTES de generar la respuesta, no como contexto opcional.
- No cargar skills SDD (`sdd-*`) salvo que el flujo SDD esté activo o lo pida el orquestador.

## Decision Gates

| Tarea | Skill |
|---|---|
| Modelos/ORM/DRF/tests Django | `django-expert` |
| UI/frontend/Tabler | `frontend-design` |
| Accesibilidad/auditoría | `web-design-guidelines` |
| Feature con spec→plan→tasks | flujo SDD (`sdd-*`) |
| PR/commits/issue | `branch-pr`, `work-unit-commits`, `issue-creation` |
| Crear/mejorar skills | `skill-creator`, `skill-improver` |
| Ninguna coincide | Trabajar directo, sin skill |

## Execution Steps

1. Mapear la tarea a la tabla de decisión.
2. Cargar la skill elegida antes de trabajar.
3. Si ninguna coincide, proceder sin skill.

## Output Contract

- Skill cargada y aplicada, o justificación de por qué no se cargó ninguna.

## References

- `../../AGENTS.md` — contexto y convenciones del proyecto.
