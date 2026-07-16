# 004 · Modelos y satélites

**Estado:** implementado ✅

## Qué hace

Visualización interactiva de productos meteorológicos: mapas del modelo WRF (seleccionables por variable y hora), meteogramas con selector de municipio, sondeos aerológicos (Skew-T) con generación de gráficos, imágenes satelitales GOES-16 (5 canales) con proxy que evita CORS, y descarga de animaciones GIF desde frames del modelo.

## Por qué

Los meteorólogos necesitan acceder a salidas de modelos numéricos e imágenes satelitales para elaborar pronósticos. Integrarlas en el portal evita tener que abrir aplicaciones externas y centraliza el flujo de trabajo.

## Criterios de aceptación

- [x] Mapas WRF: selector de fecha/hora/variable → proxy de imágenes con whitelist de dominio.
- [x] Meteograma: selector de municipio + fecha → gráfico generado por HighCharts con datos de API externa.
- [x] Sondeo Skew-T: selector de municipio + fecha + índice → gráfico generado con PIL/base64.
- [x] Descarga de GIF animado: frames del modelo ensamblados con PIL (máx 72h/25 frames).
- [x] Proxy de imágenes satelitales: 5 canales GOES-16 desde `tropic.ssec.wisc.edu` vía proxy corporativo.
- [x] Proxy con validación: whitelist de paths, validación de content-type, bloqueo de redirecciones.
- [x] Protección SSRF en proxy de modelo: resolución de IP, bloqueo de loopback/link-local/multicast.

## Fuera de alcance

- Modelos globales distintos a WRF (GFS, ECMWF).
- Suscripción a alertas basadas en modelos.
- Visualización en tiempo real (streaming).
