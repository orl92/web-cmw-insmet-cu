// Auto-refresco de la tabla de tareas: el operador ve el progreso del worker
// sin recargar la página.
//
// Tres decisiones que no son obvias y conviene no romper:
//
// 1. Se sondea una huella (?fingerprint=1), no la tabla. La huella es un token
//    barato; la tabla entera solo se descarga y se repinta cuando el token se
//    movió. Preguntar "¿cambió algo?" cada 5s es barato; renderizar el partial
//    completo cada 5s para reemplazar filas idénticas es trabajo tirado.
//
// 2. Se recarga el `tbody` vía un partial (?partial=1) y se repuebla la
//    instancia de DataTables existente, igual que la auditoría. Redibujar la
//    tabla entera perdería el orden, la búsqueda y la paginación del operador
//    en cada pasada.
//
// 3. El polling se pausa si el operador está interactuando: ordenando una
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
      url: tableEl.getAttribute('data-language-url') || '',
      emptyTable: 'No hay tareas registradas.'
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
  var lastToken = null;

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

  function currentParams() {
    var params = new URLSearchParams(window.location.search);
    return params;
  }

  // Sondeo barato: solo devuelve un token, no renderiza la página.
  function pollFingerprint() {
    if (stopped) return Promise.resolve(null);
    if (document.hidden) return Promise.resolve(null);
    var params = currentParams();
    params.set('fingerprint', '1');

    return fetch(baseUrl + '?' + params.toString(), {
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
      .then(function (response) {
        if (!response.ok) throw new Error('Error al consultar el estado');
        return response.json();
      })
      .then(function (data) {
        return data.token || null;
      })
      .catch(function (err) {
        // Un fallo puntual de red no debe romper el polling: el siguiente ciclo
        // reintenta solo. Se registra, no interrumpe.
        console.warn('[tasks-monitor] No se pudo consultar la huella:', err);
        return null;
      });
  }

  // Un solo camino para meter un partial en la tabla. Lo usan el polling y los
  // botones de filtro: si cada uno tuviera el suyo, se desincronizarían (el
  // forgotó los modales, el otro olvidó resetear la huella, etc.).
  function applyPartial(doc) {
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

    // El form de reintento se renderiza DENTRO del <td> de acciones, así que
    // viaja con la fila cuando DataTables hace cell.innerHTML: el botón
    // `form="retry-N"` siempre encuentra su form. Por eso no hace falta
    // sincronizar forms aparte.
    //
    // Los modales de traceback sí viven fuera del tbody, en un contenedor
    // aparte: sin repoblarlos, una fila que pasa a ERROR con la página abierta
    // tendría su botón apuntando a un modal inexistente.
    syncTracebackModals(doc);
    reiniciarTooltips();
  }

  // Devuelve `true` si el partial se aplicó, `false` si falló. Un solo punto de
  // captura para los dos caminos: el polling solo necesita que no se rompa, pero
  // los filtros SÍ necesitan saber si el cuerpo llegó antes de cambiar la URL —
  // si no, la barra de direcciones anunciaría un filtro que la tabla nunca llegó a
  // mostrar.
  function fetchPartial(url, errorMessage) {
    return fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
      .then(function (response) {
        if (!response.ok) throw new Error(errorMessage);
        return response.text();
      })
      .then(function (html) {
        applyPartial(new DOMParser().parseFromString(html, 'text/html'));
        return true;
      })
      .catch(function (err) {
        console.warn('[tasks-monitor]', err);
        return false;
      });
  }

  function refreshTable() {
    var params = currentParams();
    params.set('partial', '1');
    return fetchPartial(baseUrl + '?' + params.toString(), 'Error al refrescar la tabla');
  }

  // El ciclo: primero la huella barata, y solo si cambió, la tabla.
  function tick() {
    if (stopped) return;
    // Mientras el operador está usando la tabla no se avanza ni el token: si
    // se avanzara, el cambio se daría por visto sin haberse visto, y al
    // retomar la poll no se pintaría nunca.
    if (shouldSkip()) return;

    pollFingerprint().then(function (token) {
      if (token === null) return;
      if (lastToken === null) {
        // Primera pasada tras cargar la página: lo que hay en pantalla ya es
        // lo último, así que no hay nada que descargar todavía.
        lastToken = token;
        return;
      }
      if (token === lastToken) return;
      return refreshTable().then(function () {
        lastToken = token;
      });
    });
  }

  // Los botones de filtro (Todos / Errores / En cola) cambian la tabla sin
  // recargar la página. Antes eran <a href> que recargaban todo, y en una tabla
  // que se refresca sola eso tiraba el estado del operador a la basura.
  function marcarFiltroActivo(url) {
    var status = new URL(url, window.location.origin).searchParams.get('status') || '';
    document.querySelectorAll('[data-tasks-filter]').forEach(function (link) {
      var suyo = new URL(link.href, window.location.origin).searchParams.get('status') || '';
      link.classList.toggle('active', suyo === status);
    });
  }

  function aplicarFiltro(url) {
    var destino = new URL(url, window.location.origin);
    destino.searchParams.set('partial', '1');

    return fetchPartial(destino.toString(), 'Error al filtrar las tareas').then(function (ok) {
      if (!ok) return;
      // La URL se actualiza para que recargar o compartir la página conserve el
      // filtro, y para que el polling siga leyendo los params actuales.
      window.history.pushState({}, '', url);
      marcarFiltroActivo(url);
      // La línea base de la huella es la del filtro nuevo: sin resetearla, la
      // próxima pasada vería un token distinto y descargaría la tabla dos
      // veces seguidas.
      lastToken = null;
    });
  }

  document.querySelectorAll('[data-tasks-filter]').forEach(function (link) {
    link.addEventListener('click', function (e) {
      e.preventDefault();
      aplicarFiltro(link.getAttribute('href'));
    });
  });

  // Volver atrás (o adelante) debe pintar la tabla, no dejarla mintiendo: la
  // URL ya cambió sola, así que hay que volver a pedir el partial.
  window.addEventListener('popstate', function () {
    aplicarFiltro(window.location.pathname + window.location.search);
  });

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

  var interval = setInterval(tick, POLL_MS);
  window.addEventListener('beforeunload', function () {
    stopped = true;
    clearInterval(interval);
  });
});
