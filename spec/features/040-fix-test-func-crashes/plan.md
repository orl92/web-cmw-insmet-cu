# Plan — 040-fix-test-func-crashes

## Enfoque técnico
Las 3 vistas copiaron un `test_func()` de otra vista que tenía campo `user`, pero el modelo destino no lo tiene.

### ForecastUpdateView (views.py:194)
```python
# Cambiar de:
def test_func(self):
    return self.request.user.is_superuser or self.get_object().user == self.request.user
# A:
def test_func(self):
    return self.request.user.is_superuser
```

### EmailRecipientListUpdateView (views.py:131)
```python
# Cambiar de:
def test_func(self):
    listado = self.get_object()
    return self.request.user.is_superuser or listado.user == self.request.user
# A: eliminar UserPassesTestMixin, dejar que PermissionRequiredMixin maneje el permiso.
# Si no tiene permiso específico, cambiar a solo superuser.
```

### GroupUpdateView (accounts/views/group/views.py:226)
```python
# Cambiar de:
def test_func(self):
    return self.request.user.is_superuser or self.get_object().user == self.request.user
# A:
def test_func(self):
    return self.request.user.is_superuser
```

## App(s) modificadas
- dashboard/views/pronosticos/views.py
- dashboard/views/email_recipient/views.py
- accounts/views/group/views.py
