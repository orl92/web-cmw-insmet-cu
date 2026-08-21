# Spec — 061-models-conventions

## Criterios de Aceptación

1. `Invoice` y `Certificate` heredan de `FileHandlerMixin` y tienen
   `file_fields` definido.
2. Todos los modelos concretos no-abstractos tienen `Meta.ordering`.
3. Todos los `ForeignKey`/`OneToOneField` tienen `related_name` explícito.
4. `SiteConfiguration` no declara `id = AutoField(primary_key=True)` redundante.
5. No se rompen tests existentes tras los cambios.
6. Migraciones generadas y ejecutadas.
