# Plan — 046-weatherreport-refactor

## Enfoque técnico
1. Renombrar campo `type` → `report_type` en WeatherReport model
2. Actualizar todas las referencias: forms, vistas, templates, API serializer
3. Ejecutar `makemigrations`
4. Optimizar `form_valid()`: guardar una vez con `form.save()` directamente

## App(s) modificadas
- dashboard/models.py
- dashboard/views/tiempo/views.py
- dashboard/forms/tiempo/forms.py (si aplica)
- api/serializers.py (si aplica)
- templates que referencien `object.type`
