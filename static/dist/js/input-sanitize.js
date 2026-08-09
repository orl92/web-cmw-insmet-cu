document.addEventListener('DOMContentLoaded', function () {
  var SANITIZERS = {
    phone: function (value) { return value.replace(/[^\d\s,\-;]/g, ''); },
    nit: function (value) { return value.replace(/\D/g, ''); },
    account: function (value) { return value.replace(/\D/g, ''); },
    reeup: function (value) { return value.replace(/[^\d.]/g, ''); },
  };

  document.querySelectorAll('input[data-sanitize]').forEach(function (field) {
    field.addEventListener('input', function () {
      var type = field.getAttribute('data-sanitize');
      var sanitize = SANITIZERS[type];
      if (!sanitize) {
        return;
      }
      field.value = sanitize(field.value);
      if (field.classList.contains('is-invalid') && field.checkValidity()) {
        field.classList.remove('is-invalid');
      }
    });
  });
});
