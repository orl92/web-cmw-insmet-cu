# 088-seguridad-critica · Seguridad crítica

## Motivación

Auditoría de seguridad encontró problemas activos y explotables:

1. **Credenciales FTP hardcodeadas** en `apps/api/data/FileObs.py:22-24` (host `10.0.100.224`, usuario `estaciones`, password `CasaB2024*`) — secreto real versionado en el repo. `detect-secrets` no lo atrapó por no ser formato de clave estándar.
2. **Rate limiting declarado pero inexistente** — `config/settings.py:275` define `DEFAULT_THROTTLE_RATES` pero no hay `DEFAULT_THROTTLE_CLASSES` ni `throttle_classes` en ninguna vista API. Todas usan `AllowAny`. El claim de AGENTS.md ("100/h anon, 1000/h user") es falso.
3. **Endpoints públicos sin auth**: `ExcelJSONView` (`apps/meteo/views/forecast.py:283`, `csrf_exempt`, parsea Excel arbitrario sin login), `ajax_pending_subscriptions` (`apps/commercial/views/invoices.py:405`, fuga de datos de cualquier cliente sin login), proxys de imagen/GIF (`apps/home/views/modelos/views.py` y `satelites/views.py:20`), `DescargarGifView` (baja 25 imágenes por request).
4. **Bug ASGI**: `config/asgi.py:14` usa `'config .settings'` (espacio) → cualquier deploy ASGI falla.
5. **Open redirect** en `apps/user_auth/views/login.py:23-25` (`next` sin validación de host permitido).
6. **Backend de correo para certificado autofirmado** — `config/custom_email_backend.py` (`CustomSTARTTLSBackend`) desactiva la verificación TLS (`ssl.CERT_NONE`) porque el servidor de correo del proyecto usa un certificado autofirmado. NO es dead code: `config/settings.py` lee `EMAIL_BACKEND` desde env, y `generate_env.py` lo escribe apuntando al backend custom cuando el correo es autofirmado. El hallazgo original Q lo marcó como dead code porque el `.env` no seteaba `EMAIL_BACKEND`.

## Solución

### 1. Credenciales FTP a variables de entorno
- Mover `HOST`, `USER`, `PASS` de `FileObs.py` a `.env` (nuevas variables `FTP_OBS_HOST`, `FTP_OBS_USER`, `FTP_OBS_PASS`).
- Leerlas en `config/settings.py` y pasarlas al backend de datos (por constructor o parámetro, sin importar settings desde el paquete data si genera ciclo — usar `django.conf.settings` con lazy access o un settings holder).
- Eliminar los literales del código.
- Documentar **rotación manual de la password** (quedó versionada en git history) como paso de despliegue obligatorio: cambiar la password en el servidor FTP cuando haya acceso.
- Actualizar `.secrets.baseline` si `detect-secrets` lo detecta.

### 2. Rate limiting real
- Agregar `DEFAULT_THROTTLE_CLASSES` en `REST_FRAMEWORK` de `config/settings.py`.
- Mantener `DEFAULT_THROTTLE_RATES` (anon 100/h, user 1000/h).
- Endpoints de proxys/imágenes pesados pueden tener throttle más estricto por vista si aplica.

### 3. Auth en endpoints expuestos
- `ExcelJSONView`: agregar `LoginRequiredMixin` + `PermissionRequiredMixin` con `meteo.change_forecast` (o permiso equivalente documentado) y **remover `csrf_exempt`** (o mantener solo si el cliente lo requiere, documentando el riesgo).
- `ajax_pending_subscriptions`: agregar `@login_required` + `@permission_required('commercial.view_servicesubscription')`, y validar que el `customer_id` pertenece al usuario (o que es staff/superuser).
- Proxys de imagen/GIF y `DescargarGifView`: mantener públicos (son el portal público) pero **agregar rate limit por IP** (ver opciones abajo) y validar tamaño/máximo de descargas.

### 4. Fix ASGI
- `config/asgi.py:14` → `'config.settings'` (quitar el espacio).

### 5. Open redirect
- Validar el parámetro `next` contra el host actual (o lista `ALLOWED_HOSTS`): solo permitir rutas relativas que no empiecen con `//` ni contengan `://`.

### 6. Backend de correo (certificado autofirmado)
- Mantener `config/custom_email_backend.py` (`CustomSTARTTLSBackend`): el servidor de correo del proyecto usa certificado autofirmado, por lo que se requiere desactivar la verificación TLS.
- `config/settings.py` ya lee `EMAIL_BACKEND` desde env; `generate_env.py` (modo interactivo) lo escribe apuntando al backend custom cuando el correo es autofirmado.
- `EMAIL_USE_TLS=True` se mantiene en settings.

## Rate limiting para endpoints públicos

Opciones evaluadas:
- **`django-ratelimit`**: decorador `@ratelimit(key='ip', rate='100/h')` — simple, por vista.
- **Middleware de throttling DRF solo aplica a la API**, no a vistas Django normales.
- Recomendación: `django-ratelimit` para proxys/imágenes/ExcelJSON si se mantiene público.

## Criterios de aceptación

- [ ] `FileObs.py` no contiene literales de credenciales; lee de env/settings.
- [ ] `.env`/`env.sample` documentan `FTP_OBS_*`; `generate_env` los genera.
- [ ] Rotación manual documentada en el spec y en README o SECURITY.md.
- [ ] `DEFAULT_THROTTLE_CLASSES` presente en settings; request anónimo a `/api/` >100/h recibe 429.
- [ ] `ExcelJSONView` requiere login (o tiene rate limit si se decide público).
- [ ] `ajax_pending_subscriptions` requiere login y solo expone suscripciones propias (staff ve todas).
- [ ] Proxys de imagen con rate limit por IP.
- [ ] `config/asgi.py` con `'config.settings'` correcto.
- [ ] `next` en login solo redirige a rutas relativas seguras.
- [ ] Backend de correo custom eliminado (o conectado con TLS forzado).
- [ ] `python manage.py check` y `python manage.py test` pasan.
