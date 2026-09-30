# Tasks

## 1. Sincronizar el spec con la realidad

- [x] 1.1 Auditar `013-check-deploy-ci` contra el código actual y listar cada
      requirement que contradice la realidad
- [x] 1.2 Delta spec: `REMOVED` del requirement del fallback efímero
- [x] 1.3 Delta spec: `MODIFIED` de los dos requirements que nombran
      `manage.py generate_env` (`CI Generates Its Own Secret Key Material`,
      `Production Rejects The Console Email Backend`)
- [x] 1.4 Delta spec: `ADDED` de los tres requirements que fijan el diseño
      (generador fuera de Django, fail-closed, clave de descifrado separada)

## 2. Verificar que el delta describe el código, no la intención

- [x] 2.1 `EphemeralSecretKeyWarning` no aparece en ningún `.py`
- [x] 2.2 `base.load_secret_key()` levanta `ImproperlyConfigured` en los cuatro
      casos sin par descifrable, y no hay fallback
- [x] 2.3 El perfil `testing` inyecta el par determinista antes de importar `base`
- [x] 2.4 El mensaje del console-email nombra `scripts/generate_env.py --production`
- [x] 2.5 El job `deploy-check` invoca el generador y escribe el `.env` fuera del
      checkout
- [x] 2.6 Los units cargan `EnvironmentFile=-/etc/webcmp/encryption.env`

## 3. Cerrar

- [x] 3.1 `python manage.py test apps.core` (259 tests, OK)
- [x] 3.2 `python manage.py check` (0 issues)
- [ ] 3.3 Commit
- [ ] 3.4 Archivar con `gentle-ai sdd-archive` para promover el delta sobre
      `openspec/specs/013-check-deploy-ci/`

## Nota

Sin cambios de código: este change solo sincroniza el contrato. Si al archivar
algún requirement del delta no coincide con el código, el bug está en el código
o en el delta, y se resuelve antes de promover.
