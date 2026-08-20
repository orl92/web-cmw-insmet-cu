---
name: web-design-guidelines
description: "Trigger: accesibilidad, auditoría UI, WCAG, contraste, usabilidad. Auditar accesibilidad y usabilidad de interfaces del proyecto."
license: Apache-2.0
metadata:
  author: "yoelvismr"
  version: "1.1"
---

# Skill: web-design-guidelines

## Activation Contract

Cargar al auditar accesibilidad, contraste, navegación por teclado, HTML semántico o usabilidad de cualquier vista. Frases típicas: "revisá mi UI", "check accessibility", "audit design", "review UX".

## How It Works

1. Leer los archivos especificados (o pedir al usuario el archivo/patrón si no los da).
2. Verificar contra las reglas de abajo (autocontenidas, siempre disponibles).
3. Opcional: si hay red disponible, refrescar las reglas desde Web Interface Guidelines (fuente de reglas oficiales, formato de salida incluido) en `https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md` — usar solo como complemento, nunca como requisito.
4. Reportar hallazgos en el formato terso `archivo:línea`.

## Hard Rules

- HTML semántico: `header`, `nav`, `main`, `section`, `footer` en layouts.
- Formularios: `<label>` asociado a cada campo; mensajes de error legibles y asociados.
- Contraste AA mínimo (4.5:1 texto normal, 3:1 texto grande).
- Navegación completa por teclado: focus visible en todos los elementos interactivos.
- Alt text descriptivo en imágenes; iconos decorativos con `aria-hidden`.
- No depender solo del color para transmitir estado (errores, warnings).

## Decision Gates

| Hallazgo | Acción |
|---|---|
| Contraste insuficiente | Ajustar color del tema Tabler; verificar AA |
| Falta label | Agregar `<label for>` o `aria-label` |
| Sin focus visible | Revisar estilos de `:focus-visible` del tema |
| Tabla sin encabezados | `<th scope>` correcto |

## Execution Steps

1. Recorrer la vista con teclado (Tab, Enter, Escape).
2. Inspeccionar contraste y semántica en el DOM.
3. Listar hallazgos con severidad (CRITICAL/WARNING/SUGGESTION).
4. Corregir solo lo del alcance pedido y re-verificar.

## Output Contract

- Lista de hallazgos con severidad y ubicación en `archivo:línea`.
- Correcciones aplicadas (si el alcance lo pide).
- Re-verificación de los puntos corregidos.

## References

- `../../AGENTS.md` — convenciones UI (Tabler, español, templates).
- Web Interface Guidelines (opcional, requiere red): `https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md`
