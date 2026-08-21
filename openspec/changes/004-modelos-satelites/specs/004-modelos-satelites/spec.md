# Spec — 004-modelos-satelites

## Criterios de aceptación

- [x] Mapas WRF: selector de fecha/hora/variable → proxy de imágenes con whitelist de dominio.
- [x] Meteograma: selector de municipio + fecha → gráfico generado por HighCharts con datos de API externa.
- [x] Sondeo Skew-T: selector de municipio + fecha + índice → gráfico generado con PIL/base64.
- [x] Descarga de GIF animado: frames del modelo ensamblados con PIL (máx 72h/25 frames).
- [x] Proxy de imágenes satelitales: 5 canales GOES-16 desde `tropic.ssec.wisc.edu` vía proxy corporativo.
- [x] Proxy con validación: whitelist de paths, validación de content-type, bloqueo de redirecciones.
- [x] Protección SSRF en proxy de modelo: resolución de IP, bloqueo de loopback/link-local/multicast.
