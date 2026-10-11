// Estados en vivo de los listados de facturación y suscripciones.
//
// DataTables pagina en el cliente sobre filas ya renderizadas, así que no hace
// falta redibujar nada: el endpoint devuelve el HTML de las celdas Estado y
// Acciones y este script reemplaza el innerHTML de esas celdas. Sólo consulta
// mientras existan filas en estado transitorio (PDF/correo pendientes) y se
// pausa en pestaña oculta para no gastar requests a ciegas.
(function () {
  'use strict';

  var DEFAULT_INTERVAL_MS = 10000;
  var MAX_CONSECUTIVE_FAILURES = 5;

  function initListLiveStatus(cfg) {
    if (!cfg || !cfg.url) return;
    if (!document.querySelectorAll('[data-live-status]').length) return;
    // Sin ninguna fila transitoria no hay nada que refrescar.
    if (!document.querySelectorAll('[data-live-pending]').length) return;

    var intervalMs = cfg.intervalMs || DEFAULT_INTERVAL_MS;
    var maxFailures = cfg.maxFailures || MAX_CONSECUTIVE_FAILURES;
    var failures = 0;
    var stopped = false;
    var timer = null;
    var inFlight = false;

    function pendingUuids() {
      var seen = {};
      var out = [];
      var cells = document.querySelectorAll('[data-live-status][data-uuid][data-live-pending]');
      Array.prototype.forEach.call(cells, function (cell) {
        var value = cell.getAttribute('data-uuid');
        if (value && !seen[value]) {
          seen[value] = true;
          out.push(value);
        }
      });
      return out;
    }

    function patchRow(row) {
      if (!row || !row.uuid) return;
      var statusCell = document.querySelector('[data-live-status][data-uuid="' + row.uuid + '"]');
      var actionsCell = document.querySelector('[data-live-actions][data-uuid="' + row.uuid + '"]');
      if (statusCell) {
        if (typeof row.status_html === 'string') statusCell.innerHTML = row.status_html;
        // La fila deja de ser transitoria: se quita la marca para que el próximo
        // ciclo no la vuelva a pedir.
        if (row.pending) statusCell.setAttribute('data-live-pending', '1');
        else statusCell.removeAttribute('data-live-pending');
      }
      if (actionsCell && typeof row.actions_html === 'string') {
        actionsCell.innerHTML = row.actions_html;
      }
    }

    function schedule() {
      if (stopped || document.hidden || timer) return;
      timer = window.setTimeout(function () {
        timer = null;
        tick();
      }, intervalMs);
    }

    function tick() {
      if (stopped || inFlight) return;
      var uuids = pendingUuids();
      if (!uuids.length) {
        stopped = true;
        return;
      }
      inFlight = true;
      var separator = cfg.url.indexOf('?') === -1 ? '?' : '&';
      fetch(cfg.url + separator + 'uuids=' + encodeURIComponent(uuids.join(',')), {
        credentials: 'same-origin',
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        cache: 'no-store'
      })
        .then(function (response) {
          if (!response.ok) throw new Error('HTTP ' + response.status);
          return response.json();
        })
        .then(function (data) {
          inFlight = false;
          failures = 0;
          (data.rows || []).forEach(patchRow);
          // Sin transitorios el estado ya es estable: cortar el polling.
          if (data.pending) schedule();
          else stopped = true;
        })
        .catch(function () {
          inFlight = false;
          failures += 1;
          if (failures >= maxFailures) {
            stopped = true;
            return;
          }
          schedule();
        });
    }

    // Pausa en pestaña oculta; al volver, un ciclo inmediato retoma el estado.
    document.addEventListener('visibilitychange', function () {
      if (document.hidden) {
        if (timer) {
          window.clearTimeout(timer);
          timer = null;
        }
      } else if (!stopped) {
        tick();
      }
    });

    tick();
  }

  window.initListLiveStatus = initListLiveStatus;
})();