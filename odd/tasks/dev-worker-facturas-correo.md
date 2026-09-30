# Worker de facturas y correos en desarrollo

## Objetivo

Poder probar en desarrollo el flujo completo de generación de PDF de factura y envío
de correo, y ver un resultado real —un artefacto que se pueda abrir— en vez de un
`email_sent=True` que no llegó a ningún lado.

## Problema

El flujo está apilado sobre cuatro fallas que se.maskan entre sí. Por eso parece
"simulado" cuando en realidad nada llega a ejecutarse.

1. **Falta el binario de PDF.** `apps/commercial/views/invoice_utils.py:72` usa
   `pdfkit.from_string(...)`, que envuelve el binario `wkhtmltopdf`. El paquete
   Python `pdfkit==1.0.0` está en `requirements/base.txt:77`, pero el binario es del
   sistema. Sin él, `pdfkit.from_string` lanza `OSError: No wkhtmltopdf executable
   found`, y ese error no dice qué instalar.

2. **La tarea del worker muere antes de enviar.** En `apps/core/tasks.py:23-31` el
   PDF se genera primero y `enviar_correo_factura` se llama después. Con el paso 1
   fallando, la excepción sale de la tarea y el correo nunca se intenta. Huey reintenta
   3 veces con `retry_delay=30` y `retry_backoff=True`, así que el síntoma es un log
   de reintentos, no un error visible.

3. **El worker no arranca en un clon limpio.** `run_huey.sh` escribe en
   `logs/huey.log` y el directorio no existe. `.gitignore:11` tiene `*/logs/*`, que
   excluye el contenido pero no crea el directorio. El README dice "correr
   `./run_huey.sh` en otra terminal"; ese comando falla.

4. **El console backend no puede fallar.** `config/settings/dev.py:30-31` lo elige
   cuando el entorno está en silencio. `email.send()` nunca levanta, así que
   `enviar_correo_factura` pone `email_sent=True` e `invoice.save()`. El correo
   entero se imprime al stdout y se descarta. Para el usuario el resultado es idéntico
   al éxito.

## Rutas de envío (el mapa que faltaba)

| Flujo | Entry point | ¿Worker? | Consecuencia |
| --- | --- | --- | --- |
| Alta de factura manual | `apps/commercial/views/invoices.py:295` | Sí, encola | La vista responde `messages.success('Factura manual generada (con suscripciones creadas)')` y redirige. El PDF y el correo pasan a ser asíncronos: si el worker no está corriendo, la tarea queda en `huey.db` para siempre y el usuario ya vio un "generada" |
| Alta de factura por lote | `apps/commercial/views/invoices.py:215` | Sí, encola | Igual que la anterior, y en lote el silencio se multiplica por N facturas |
| Reenvío de factura | `apps/commercial/views/invoices.py:460` | No, `enviar_correo_factura()` inline en el request | Bloquea el request. El error de PDF sale por `messages.error` y "Revise los logs", así que al menos es visible |
| Alerta meteorológica | `apps/core/utils.py:116` `mail_send` → `send_email_task` | Sí, encola | Sin consumer, la tarea queda en `huey.db` y el caller retorna igual |

El detalle que hace que el flujo parezca "simulado" no es que la tarea no se
encole: **se encola en las dos altas de factura**, y el worker no corre. La vista ya
devolvió un mensaje de éxito, así que el único rastro del fallo es
`logs/huey.log`, en otra terminal.

## Alcance

- [x] T1 `run_huey.sh` crea `logs/` si no existe.
- [x] T2 Preflight del binario de PDF con error accionable, en vez del `OSError` opaco
      de pdfkit.
- [x] T3 `manage.py send_test_invoice` para ejercitar la ruta del worker de punta a
      punta, con preflight de dependencias y datos.
- [x] T4 Documentar en el README cómo ver el correo real en dev (backend `filebased`
      de Django, sin dependencias nuevas) y que `wkhtmltopdf` es un requisito del
      sistema, no un paquete Python.
- [x] T5 Exponer `EMAIL_FILE_PATH` en `base.py`. Sin él, el backend `filebased` hace
      `os.path.abspath(None)` y revienta con `TypeError: expected str, bytes or
      os.PathLike object, not NoneType`, un error que no dice qué setting falta.
- [x] T6 Ignorar `tmp/` en `.gitignore`: los correos de dev llevan datos de clientes y
      no deben terminar en un commit. Ojo: el backend `filebased` escribe `.log`, no
      `.eml` (`"%s-%s.log"` en `django/core/mail/backends/filebased.py`).
- [x] T7 Extender el anti-consola de `production` a los tres backends que descartan en
      silencio (`console`, `filebased`, `locmem`). Lo encontré al documentar T4: al
      recomendar `filebased` para dev, copiar ese `.env` a producción pasaba el
      check y perdía todas las facturas sin un error. La lista vive en
      `base.silent_email_backends` para que `production` no la repita.

## Fuera de alcance

- **Mover el envío de factura al worker.** Hoy la vista lo hace inline. Es una
  decisión de arquitectura con su propio trade-off (respuesta inmediata y `email_sent`
  cierto vs. request no bloqueado), no un fix. Se documenta el estado, no se cambia.
- **Cambiar el default de `EMAIL_BACKEND` en dev.** El requirement promovido
  "Dev defaults to console only when the environment is silent" (013) lo fija
  explícitamente. Cambiarlo rompe un contrato vigente; la alternativa es documentar
  cómo cambiarlo por entorno.
- **Probar SMTP real contra un servidor.** El backend `filebased` produce artefactos
  reales pero, como el console, no puede fallar por red. Probar fallos de SMTP real
  es otro trabajo.

## Criterios de aceptación

- [x] En un clon sin `logs/`, `./run_huey.sh` arranca. Verificado borrando `logs/` y
      corriendo el script: crea el directorio y el consumer levanta.
- [x] Sin `wkhtmltopdf`, el error dice qué comando instalar, no `No wkhtmltopdf
      executable found`. Verificado en la máquina: el preflight corta antes de
      encolar y no crea datos.
- [x] `manage.py send_test_invoice <uuid>` encola la tarea del worker, informa el
      preflight y no dice "enviado" si no se envió. Verificado contra el `huey.db`
      real (con un `wkhtmltopdf` stub en `PATH` para pasar el preflight): la tarea
      aparece en la tabla `task` con el UUID de la factura y la `base_url`.
- [x] El README dice que `wkhtmltopdf` es requisito del sistema y cómo ver el correo
      real en dev.
- [x] **El consumer encuentra las tareas.** `huey_consumer config.huey.huey` no
      ejecutaba `django.setup()` y `CoreConfig.ready()` no importaba `apps.core.tasks`,
      así que el TaskRegistry nacía vacío y el worker no procesaba nada. Corregido con
      `config/huey_consumer_entry.py` (que corre `django.setup()` antes de exportar
      `huey`) y el import en `CoreConfig.ready()`. Regresión en
      `apps/core/tests/test_huey_registry.py`, que arranca un subproceso como el
      consumer: falla sin el fix, pasa con él.
- [x] **El PDF de la factura se renderiza.** `generate_invoice_pdf_standalone` pedía
      `pages/commercial/invoice/factura_template.html`, ruta que no existe: el archivo
      se renombró a `template.html` en la reestructuración 1043f55 y el código quedó
      apuntando al nombre viejo. El resultado era `TemplateDoesNotExist` SIEMPRE,
      pase lo que pase con el binario: la tarea del worker moría antes de enviar el
      correo y el fallback "Ver PDF" del listado absorbía la excepción. Regresión en
      `apps/commercial/tests/test_invoice_pdf.py`, que fija el HTML renderizado con
      `pdfkit` parcheado.
- [x] **Flujo completo por el consumer real**, con un `wkhtmltopdf` stub en `PATH`: la
      tarea se ejecutó, el PDF quedó guardado en la factura y el correo se entregó por
      `filebased` con el adjunto `application/pdf`
      (`factura_DEMO-0008_2026-09-30.pdf`). `email_sent=True`, `email_error=None`,
      cola vacía. Evidencia: `tmp/emails/20260930-095851-*.log`.
- [ ] **Pendiente, bloqueado por el sistema:** lo mismo pero con el binario real. El
      stub prueba el encadenamiento (encolado → registro → plantilla → binario →
      adjunto → flags), no la calidad del render. Requiere `sudo apt install
      wkhtmltopdf`; hasta entonces el HTML que recibe el conversor real no se
      validó.

## Lo que el E2E destapó y no era de esta feature

- **`retry_backoff=True` no hace backoff.** En `apps/core/tasks.py` la tarea se declara
  `retries=3, retry_delay=30, retry_backoff=True`, pero huey lo usa como factor
  multiplicativo (`task.retry_delay *= task.retry_backoff`, `huey/api.py:614`) y en
  aritmética `True == 1`: el delay queda fijo en 30s para los tres reintentos. No se
  tocó porque cambiar la política de reintentos es decisión de operación, no de esta
  feature.
- **La cola de dev se llena de basura del test suite.** Los tests encolan tareas con
  `http://testserver/` y UUID `00000000-...` contra el `huey.db` real (no usan base de
  prueba para el storage), y quedan ahí para siempre. El consumer se come un traceback
  por tarea y nunca llega a la tarea real. Hay que vaciar `huey.db` antes de un ensayo
  manual.
- **`huey.flush()` deja el storage inconsistente.** Después de un `flush()`, las tareas
  nuevas se escriben en la tabla `task` pero `pending()` devuelve 0 y el consumer no las
  ve. Para limpiar de verdad: borrar el archivo `huey.db` (es regenerable y está
  ignorado por git).

## Decisiones que tomo acá, y por qué

- **Backend `filebased`, no Mailpit ni `aiosmtpd`.** Django ya trae
  `django.core.mail.backends.filebased.EmailBackend`. Escribe cada mensaje como un
  archivo `.log` con el PDF adjunto adentro, no agrega dependencias, no necesita
  binario ni puerto, y funciona sin red. Para "ver resultados reales" alcanza, y el
  artefacto se abre con cualquier cliente de correo.
- **El comando encola, no ejecuta inline.** Si ejecutara inline, no probaría el worker,
  que es lo que hay que probar. Por eso lleva un flag para correr sin consumer cuando
  uno solo quiere ver el resultado rápido.
