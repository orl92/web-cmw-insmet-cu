# 004 · Modelos y satélites — Plan

## Enfoque

Vistas TemplateView con POST handler para formularios de consulta, vistas View para proxy de imágenes (con validación de seguridad), integración con APIs externas (apimet.cmw.insmet.cu, modelo.cmw.insmet.cu, tropic.ssec.wisc.edu), y generación de gráficos server-side con PIL.

## Implementación

1. **Mapas WRF**: `MapaView` — formulario con MeteoDataForm (datetime + variable), llama a `http://apimet.cmw.insmet.cu/api/simulations/`, renderiza galería de imágenes. `ImageProxyModeloView` con whitelist de dominio, resolución de IP, bloqueo SSRF.
2. **Meteograma**: `MeteogramView` — formulario con MeteogramForm (municipio + fecha), llama a `https://modelo.cmw.insmet.cu/api/meteogram/`, renderiza HighCharts con windbarb en frontend.
3. **Sondeo**: `SoundingView` — formulario con municipio + fecha + índice de pronóstico, llama a API, genera Skew-T con `generate_skewt()` de `home.data.plot_generators`, devuelve base64 PNG.
4. **GIF**: `DescargarGifView` — toma parámetros de mapa, fetches frames, ensambla GIF animado con PIL (500ms por frame).
5. **Satélites**: `SateliteView` — galería estática con 5 ítems. `ProxyImageView` — whitelist de 5 paths, proxy corporativo `http://proxy.cmw.insmet.cu:3128`, validación content-type `image/*`.

## Decisiones

- **Proxy server-side vs cliente-side** — necesario porque los dominios externos no tienen CORS; el proxy Django actúa como intermediario.
- **Whitelist estricta en proxy** — paths fijos para evitar SSRF y content injection; no se aceptan URLs dinámicas del usuario.
- **HighCharts para meteograma** — mejor visualización de wind barbs que librerías Python. La API devuelve datos JSON, el frontend grafica.

## Riesgos

- **APIs externas caídas** — las vistas muestran error y sugieren reintentar; no bloquean el resto del portal.
- **Proxy corporativo caído** — las imágenes satelitales no cargarán; el proxy está configurado como gateway obligatorio.
- **GIF muy grande** — límite de 25 frames (72h) para evitar DoS por consumo de memoria en PIL.
