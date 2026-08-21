# Feature 054 — Ofuscar emails en publicaciones científicas

## Qué hace
El email de los autores en `publicaciones.html` se muestra en texto plano, exponiéndolo a scrapers y spammers. Se ofusca sin afectar la experiencia del usuario.

## Criterios de aceptación

1. El email del autor ya no aparece en texto plano en el HTML fuente.
2. Se ve igual visualmente (se renderiza correctamente).
3. El usuario puede seguir viendo o copiando el email si es necesario (ej: tooltip o JS inversion).
