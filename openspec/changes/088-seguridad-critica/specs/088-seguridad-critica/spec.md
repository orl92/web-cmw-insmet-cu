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
