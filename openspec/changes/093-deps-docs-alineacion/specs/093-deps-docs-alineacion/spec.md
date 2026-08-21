## Criterios de aceptación

- [ ] `requirements.txt` fija TODAS las deps (sin `>=` sueltos) y la versión de Django coincide con la documentación.
- [ ] AGENTS.md/CI/documentación dicen la versión real instalada.
- [ ] `env.sample` cubre exactamente las variables que settings lee (auditado).
- [ ] `generate_env.py` genera el mismo conjunto.
- [ ] Choices de warning/estado unificados en un solo lugar.
- [ ] Dependencias sin uso eliminadas.
- [ ] `python manage.py check` y `python manage.py test` pasan.
