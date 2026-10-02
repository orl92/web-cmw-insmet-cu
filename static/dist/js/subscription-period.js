/**
 * Vista previa del vencimiento de una suscripción (B2/B3).
 *
 * La unidad no se elige: sale de la categoría del servicio, que el formulario
 * publica en cada <option> como data-period-unit. El navegador sólo recalcula
 * la fecha para que el operador vea el resultado mientras edita; el valor que
 * se guarda siempre lo deriva el servidor.
 *
 * Sin JavaScript el vencimiento se imprime renderizado desde el servidor, así
 * que este archivo es una mejora de la vista previa, no un requisito.
 */
(function () {
  'use strict';

  var SERVICE_ID = 'id_service';
  var START_ID = 'id_start_date';
  var QUANTITY_ID = 'id_quantity';
  var LABEL_SELECTOR = '[data-period-quantity-label]';
  var PREVIEW_ID = 'end-date-preview';
  var PREVIEW_EMPTY = 'Se calcula con la fecha de inicio y la cantidad.';

  // Valores de `Service.get_billing_period_display()`: en singular.
  var UNIT_MONTH = 'mes';
  var UNIT_DAY = 'día';

  function byId(id) {
    return document.getElementById(id);
  }

  function pad(value) {
    return String(value).padStart(2, '0');
  }

  function parseStart(value) {
    // El picker escribe dd/mm/aaaa hh:mm AM/PM; el servidor manda ese mismo
    // formato, así que es lo único que hay que entender aquí.
    var match = /^(\d{2})\/(\d{2})\/(\d{4})\s+(\d{1,2}):(\d{2})(?:\s*([AP]M))?$/i.exec((value || '').trim());
    if (!match) {
      return null;
    }
    var hours = parseInt(match[4], 10);
    var minutes = parseInt(match[5], 10);
    var meridiem = (match[6] || '').toUpperCase();
    // El picker escribe 12 h con AM/PM; sin AM/PM se acepta 24 h, que es el
    // otro formato que el servidor acepta.
    if (minutes > 59 || hours > (meridiem ? 12 : 23) || (meridiem && hours < 1)) {
      return null;
    }
    if (meridiem === 'PM' && hours < 12) {
      hours += 12;
    } else if (meridiem === 'AM' && hours === 12) {
      hours = 0;
    }
    var date = new Date(
      parseInt(match[3], 10),
      parseInt(match[2], 10) - 1,
      parseInt(match[1], 10),
      hours,
      minutes
    );
    // Rechaza fechas imposibles que el navegador normaliza (31/02, 25:00).
    if (date.getMonth() !== parseInt(match[2], 10) - 1 || date.getDate() !== parseInt(match[1], 10)) {
      return null;
    }
    return date;
  }

  function daysInMonth(year, month) {
    return new Date(year, month + 1, 0).getDate();
  }

  function addMonths(date, months) {
    // `setMonth` desborda (31/01 + 1 mes = 03/03), así que se recorta al último
    // día del mes destino: 31/01 + 1 mes = 28/02, igual que hace relativedelta.
    var result = new Date(date.getTime());
    var day = result.getDate();
    var targetMonth = result.getMonth() + months;
    var year = result.getFullYear();
    var month = ((targetMonth % 12) + 12) % 12;
    year += Math.floor(targetMonth / 12);
    result.setFullYear(year, month, Math.min(day, daysInMonth(year, month)));
    return result;
  }

  function format(date) {
    var hours = date.getHours();
    var h12 = hours % 12;
    if (h12 === 0) {
      h12 = 12;
    }
    return pad(date.getDate()) + '/' + pad(date.getMonth() + 1) + '/' + date.getFullYear() +
      ' ' + pad(h12) + ':' + pad(date.getMinutes()) + ' ' + (hours >= 12 ? 'PM' : 'AM');
  }

  function unitOf(serviceSelect) {
    if (!serviceSelect || !serviceSelect.value) {
      return '';
    }
    var option = serviceSelect.options[serviceSelect.selectedIndex];
    return (option && option.dataset.periodUnit) || '';
  }

  function pluralize(unit, quantity) {
    if (unit === UNIT_MONTH) {
      return quantity === 1 ? UNIT_MONTH : 'meses';
    }
    return quantity === 1 ? UNIT_DAY : 'días';
  }

  function init() {
    var serviceSelect = byId(SERVICE_ID);
    var startInput = byId(START_ID);
    var quantityInput = byId(QUANTITY_ID);
    var label = document.querySelector(LABEL_SELECTOR);
    var preview = byId(PREVIEW_ID);
    if (!serviceSelect || !startInput || !quantityInput || !preview) {
      return;
    }

    function update() {
      var unit = unitOf(serviceSelect);
      var quantity = parseInt(quantityInput.value, 10);

      if (label) {
        label.textContent = unit
          ? 'Cantidad de ' + pluralize(unit, quantity)
          : 'Cantidad';
      }

      var start = parseStart(startInput.value);
      if (!unit || !start || !quantity || quantity < 1) {
        preview.textContent = PREVIEW_EMPTY;
        return;
      }

      preview.textContent = format(
        unit === UNIT_MONTH ? addMonths(start, quantity) : new Date(start.getTime() + quantity * 86400000)
      );
    }

    serviceSelect.addEventListener('change', update);
    startInput.addEventListener('change', update);
    startInput.addEventListener('input', update);
    quantityInput.addEventListener('input', update);
    update();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();