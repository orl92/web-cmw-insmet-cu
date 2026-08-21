# Plan — 063-templates-static

## Estrategia

1. **paginate_by**: agregar `paginate_by = 20` a las 13 ListViews del
   dashboard que carecen de él. Para las home ListViews (servicios públicos y
   comerciales) mantener `paginate_by = 10` (es público, menor densidad) o
   unificarlo a 20 si no hay razón para diferenciar.

2. **Bloques comentados**: hacer un grep de `<!--` en templates HTML y
   remover bloques de desarrollo muertos.

3. **Alt text**: buscar `<img` sin `alt` en todos los templates y agregar
   `alt` descriptivo (puede ser dinámico desde el contexto).

4. **Aria labels**: revisar inputs sin label asociado.

## Orden recomendado

1. paginate_by (bajo riesgo, alta visibilidad)
2. Bloques comentados (riesgo mínimo)
3. Alt text (puede requerir cambios en vistas/contextos)
4. Aria labels (último, más subjetivo)

## Riesgos

- Cambiar `paginate_by` no debería romper nada (solo afecta paginación).
- Remover bloques comentados puede eliminar código que se planea
  descomentar. Revisar cada bloque antes de eliminar.
- Alt text dinámico puede requerir pasar nuevas variables al contexto.
