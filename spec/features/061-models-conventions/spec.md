# 061 — models-conventions

## Motivación

El proyecto define convenciones estrictas para modelos Django que no se siguen
consistentemente en todas las apps. Hay modelos con FileField/ImageField que
no integran `FileHandlerMixin`, modelos sin `Meta.ordering`, ForeignKey fields
sin `related_name` explícito, y redundancia en la definición de la pk.
Estandarizar evita fugas de archivos huérfanos, queries N+1 no detectables y
comportamiento inconsistente.

## Alcance

- `apps/dashboard/models.py` (todos los modelos)
- `apps/accounts/models.py`
- `apps/publications/models.py`
- `apps/common/utils.py` (FileHandlerMixin, SoftDeleteModel)

## Criterios de Aceptación

1. `Invoice` y `Certificate` heredan de `FileHandlerMixin` y tienen
   `file_fields` definido.
2. Todos los modelos concretos no-abstractos tienen `Meta.ordering`.
3. Todos los `ForeignKey`/`OneToOneField` tienen `related_name` explícito.
4. `SiteConfiguration` no declara `id = AutoField(primary_key=True)` redundante.
5. No se rompen tests existentes tras los cambios.
6. Migraciones generadas y ejecutadas.
