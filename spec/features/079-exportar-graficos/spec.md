# 079 — exportar-graficos

## Motivación

Los charts ApexCharts del dashboard (ingresos, suscripciones, temperaturas) no tienen opción de exportar como imagen. Los usuarios (dirección del centro) necesitan incluir estos gráficos en reportes.

## Alcance

- Agregar botón "Exportar como PNG" en cada chart del dashboard
- Usar `ApexCharts.exportChart()` o canvas-to-image
- Opcional: botón "Exportar todo" que genera ZIP con todos los charts

## Criterios de Aceptación

1. Cada chart tiene botón de exportar PNG
2. La imagen descargada incluye leyenda y título
3. Resolución mínima 1200x800 px
