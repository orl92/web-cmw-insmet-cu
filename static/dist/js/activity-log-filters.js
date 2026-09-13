// Filtros AJAX para la auditoría de actividad: al enviar el form (o limpiar),
// se recarga solo la tabla vía un partial (?partial=1) sin recargar la página.
document.addEventListener('DOMContentLoaded', function () {
  var form = document.getElementById('activity-log-filters');
  if (!form) return;

  var tableEl = document.getElementById(form.getAttribute('data-table-target') || 'example');
  if (!tableEl) return;
  var clearLink = document.getElementById('activity-log-clear');

  function buildUrl(params) {
    var url = form.getAttribute('action') || window.location.pathname;
    return url + '?' + params.toString();
  }

  function fetchTable(params) {
    params.set('partial', '1');
    return fetch(buildUrl(params), { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
      .then(function (response) {
        if (!response.ok) throw new Error('Error al filtrar');
        return response.text();
      })
      .then(function (html) {
        var doc = new DOMParser().parseFromString(html, 'text/html');
        // El partial (?partial=1) devuelve <table><tbody>...</tbody></table>;
        // extraemos el tbody (DOMParser descarta un tbody suelto sin table).
        var newTbody = doc.querySelector('tbody');
        if (!newTbody) throw new Error('Respuesta inválida');
        replaceTableBody(newTbody);
      })
      .catch(function (err) {
        console.error('[activity-log] No se pudo filtrar la tabla:', err);
      });
  }

  // Refresca solo el contenido de la tabla: se mantiene la misma instancia de
  // DataTables (orden, búsqueda y paginación intactos) y solo se reemplazan los
  // datos. Cada celda se inyecta como HTML (badges, truncados, etc.).
  function replaceTableBody(newTbody) {
    var table = window.dataTableInstances && window.dataTableInstances[tableEl.id];
    if (!table) return;

    var rows = Array.prototype.map.call(newTbody.querySelectorAll('tr'), function (tr) {
      return Array.prototype.map.call(tr.querySelectorAll('td'), function (td) {
        return td.innerHTML;
      });
    });

    table.clear();
    table.rows.add(rows);
    table.draw();
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    fetchTable(new URLSearchParams(new FormData(form)));
  });

  if (clearLink) {
    clearLink.addEventListener('click', function (e) {
      e.preventDefault();
      // Limpiar = estado inicial: vaciar campos y quitar filtros de la tabla.
      form.reset();
      clearPickers();
      form.querySelectorAll('input, select').forEach(function (field) {
        field.value = '';
      });
      fetchTable(new URLSearchParams());
    });
  }

  // El reset del form vacía los inputs; también sincronizamos el estado interno
  // del picker Tempus para que no conserve la fecha seleccionada.
  function clearPickers() {
    var pickers = window.tempusDominus && window.tempusDominus._instances;
    if (!pickers) return;
    form.querySelectorAll('[data-tempus]').forEach(function (input) {
      var picker = pickers[input.id];
      if (picker && typeof picker.clear === 'function') {
        picker.clear();
      }
    });
  }
});