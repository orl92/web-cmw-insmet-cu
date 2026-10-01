// Auto-refresco de la tabla de tareas: recarga solo las filas cada pocos
// segundos, para que se vea el progreso del worker sin refrescar la página.
//
// Dos decisiones que no son obvias y conviene no romper:
//
// 1. Se recarga el `tbody` vía un partial (?partial=1) y se repuebla la
//    instancia de DataTables existente, igual que la auditoría. Redibujar la
//    tabla entera perdería el orden, la búsqueda y la paginación del operador
//    en cada pasada.
//
// 2. El polling se pausa si el operador está interactuando: ordenando una
//    columna, escribiendo en la búsqueda, o con el traceback abierto. Pisar la
//    tabla en ese momento borra justo lo que la persona está por mirar. Vuelve
//    solo cuando la tabla queda quieta de nuevo.
document.addEventListener('DOMContentLoaded', function () {
  var tableEl = document.getElementById('tasks-table');
  if (!tableEl) return;

  var POLL_MS = 5000;
  var PAUSE_AFTER_IDLE_MS = 1500;
  var table = new DataTable('#tasks-table', {
    processing: true,
    language: {
      url: tableEl.getAttribute('data-language-url') || ''
    }
  });
  // La auditoría busca la instancia acá (window.dataTableInstances); se deja
  // registrado para que un JS futuro no tenga que adivinar dónde está.
  window.dataTableInstances = window.dataTableInstances || {};
  window.dataTableInstances[tableEl.id] = table;

  var baseUrl = tableEl.getAttribute('data-refresh-url') || window.location.pathname;
  var interacting = false;
  var idleTimer = null;
  var stopped = false;

  function markInteracting() {
    interacting = true;
    if (idleTimer) clearTimeout(idleTimer);
    idleTimer = setTimeout(function () {
      interacting = false;
    }, PAUSE_AFTER_IDLE_MS);
  }

  function hasOpenTraceback() {
    return !!document.querySelector('.modal.show');
  }

  // Se pausa si la tabla está ordenada a mano, si se está escribiendo en la
  // búsqueda, o si hay un modal abierto: en los tres casos, redibujar la tabla
  // borra el estado que la persona está usando.
  function shouldSkip() {
    if (interacting) return true;
    if (hasOpenTraceback()) return true;
    var order = table.order && table.order();
    if (order && order.length && order[0][0] !== 0) return true;
    var search = table.search();
    if (search) return true;
    return false;
  }

  function refreshTable() {
    if (stopped) return;
    if (shouldSkip()) return;
    if (document.hidden) return;

    var params = new URLSearchParams(window.location.search);
    params.set('partial', '1');
    var url = baseUrl + '?' + params.toString();

    fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
      .then(function (response) {
        if (!response.ok) throw new Error('Error al refrescar la tabla');
        return response.text();
      })
      .then(function (html) {
        var doc = new DOMParser().parseFromString(html, 'text/html');
        var newTbody = doc.querySelector('tbody');
        if (!newTbody) return;

        var rows = Array.prototype.map.call(newTbody.querySelectorAll('tr'), function (tr) {
          return Array.prototype.map.call(tr.querySelectorAll('td'), function (td) {
            return td.innerHTML;
          });
        });

        table.clear();
        table.rows.add(rows);
        table.draw();

        // Los formularios de reintento y los modales de traceback se
        // renderizan en el partial, fuera del tbody. Si el polling no los
        // repuebla, una fila que pasa a ERROR con la página abierta tendría su
        // botón apuntando a un modal que no existe.
        syncRetryForms(doc);
        syncTracebackModals(doc);
        reiniciarTooltips();
      })
      .catch(function (err) {
        // Un fallo puntual de red no debe romper el polling: el próximo ciclo
        // reintenta solo. Se registra, no interrumpe.
        console.warn('[tasks-monitor] No se pudo refrescar la tabla:', err);
      });
  }

  // Los <form> de reintento se renderizan en el partial junto con la tabla. El
  // polling los repuebla para que el botón no quede apuntando a un form viejo.
  function syncRetryForms(doc) {
    var nuevos = doc.querySelectorAll('form[id^="retry-"]');
    if (!nuevos.length) return;
    nuevos.forEach(function (form) {
      var viejo = document.getElementById(form.id);
      if (viejo) viejo.replaceWith(form);
    });
  }

  // Los modales de traceback dependen del estado de cada fila, así que también
  // se refrescan. Solo corresponde cuando no hay ninguno abierto (shouldSkip ya
  // lo garantiza): pisar un modal en uso lo dejaría a medias.
  function syncTracebackModals(doc) {
    var actual = document.querySelector('[data-tasks-modals]');
    var nuevo = doc.querySelector('[data-tasks-modals]');
    if (!actual || !nuevo) return;
    actual.innerHTML = nuevo.innerHTML;
  }

  // Los badges de estado y los botones cambian de clase con cada refresco, así
  // que los tooltips viejos quedan apuntando a nodos que ya no existen.
  function reiniciarTooltips() {
    var Bootstrap = (window.tabler && window.tabler.bootstrap) || window.bootstrap;
    if (!Bootstrap || !Bootstrap.Tooltip) return;
    document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(function (el) {
      try {
        var instance = Bootstrap.Tooltip.getInstance(el);
        if (instance) instance.dispose();
      } catch (e) {
        // sin instancia previa: se crea una nueva más abajo
      }
      try {
        new Bootstrap.Tooltip(el);
      } catch (e2) {
        // si el tooltip no se puede crear, la tabla sigue siendo utilizable
      }
    });
  }

  // Pausar mientras la persona interactúa con la tabla.
  tableEl.addEventListener('click', markInteracting);
  tableEl.addEventListener('keyup', function (e) {
    if (e.target.matches('.dt-search input')) markInteracting();
  });

  var interval = setInterval(refreshTable, POLL_MS);
  window.addEventListener('beforeunload', function () {
    stopped = true;
    clearInterval(interval);
  });
});
