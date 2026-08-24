document.addEventListener('DOMContentLoaded', function () {
  if (typeof window.tempusDominus === 'undefined') {
    return;
  }

  var icons = {
    time: 'ti ti-clock',
    date: 'ti ti-calendar',
    up: 'ti ti-chevron-up',
    down: 'ti ti-chevron-down',
    previous: 'ti ti-chevron-left',
    next: 'ti ti-chevron-right',
    today: 'ti ti-calendar-check',
    clear: 'ti ti-trash',
    close: 'ti ti-x',
  };

  window.tempusDominus._instances = window.tempusDominus._instances || {};

  // Convierte el valor visible del datepicker (dd/mm/yyyy o yyyy-mm-dd) a
  // formato compacto YYYYMMDD para construir strings tipo datetime_init.
  window.pickerDateToId = function (value) {
    if (!value) {
      return '';
    }
    var s = String(value).trim();
    var parts = s.split('/');
    if (parts.length === 3) {
      return parts[2] + parts[1] + parts[0];
    }
    parts = s.split('-');
    if (parts.length === 3) {
      return parts[0] + parts[1] + parts[2];
    }
    return '';
  };

  // Convierte un Date a string dd/mm/yyyy (formato visible del picker).
  window.formatPickerDate = function (date) {
    return (
      pad(date.getDate()) +
      '/' +
      pad(date.getMonth() + 1) +
      '/' +
      date.getFullYear()
    );
  };

  // Convierte un Date a string dd/mm/yyyy hh:mm AM/PM (formato visible del picker datetime).
  window.formatPickerDateTime = function (date) {
    const meridiem = date.getHours() >= 12 ? 'PM' : 'AM';
    let h = date.getHours() % 12;
    if (h === 0) h = 12;
    return (
      pad(date.getDate()) +
      '/' +
      pad(date.getMonth() + 1) +
      '/' +
      date.getFullYear() +
      ' ' +
      h +
      ':' +
      pad(date.getMinutes()) +
      ' ' +
      meridiem
    );
  };

  // Convierte el valor visible del datepicker (dd/mm/yyyy o yyyy-mm-dd) a
  // ISO (yyyy-mm-dd) para construir objetos Date de forma segura.
  window.pickerDateToIso = function (value) {
    if (!value) {
      return '';
    }
    var s = String(value).trim();
    var parts = s.split('/');
    if (parts.length === 3) {
      return parts[2] + '-' + parts[1] + '-' + parts[0];
    }
    parts = s.split('-');
    if (parts.length === 3 && parts[0].length === 4) {
      return s;
    }
    return '';
  };

  function currentTheme() {
    return document.documentElement.getAttribute('data-bs-theme') === 'dark'
      ? 'dark'
      : 'light';
  }

  function pad(value) {
    return String(value).padStart(2, '0');
  }

  // Normaliza el valor del evento change (e.date) a un Date de JS.
  // TD6 puede entregar un DateTime de Luxon (con toJSDate), un Date de JS, o un
  // array. Normalizar siempre a Date de JS evita depender de la forma interna.
  function toJsDate(value) {
    if (!value) return null;
    if (typeof value.toJSDate === 'function') return value.toJSDate(); // Luxon
    if (value instanceof Date) return value; // Date de JS
    if (Array.isArray(value) && value.length) return toJsDate(value[0]);
    // Objeto con campos sueltos (p.ej. {year, month, day, hour, minute}).
    if (typeof value.year === 'number' && typeof value.month === 'number') {
      var d = value.day != null ? value.day : value.date != null ? value.date : 1;
      var h = value.hour != null ? value.hour : 0;
      var m = value.minute != null ? value.minute : 0;
      return new Date(value.year, value.month - 1, d, h, m);
    }
    return null;
  }

  // Formatea SIEMPRE desde un Date de JS (getDate/getMonth/...), jamás desde
  // getters de Luxon, para evitar divergencias de forma según el modo.
  function canonicalFormat(date, mode) {
    var dt = toJsDate(date);
    if (!dt) return '';
    var dd = pad(dt.getDate());
    var mm = pad(dt.getMonth() + 1);
    var yyyy = dt.getFullYear();
    if (mode === 'time') {
      // 24h HH:MM; Django parsea %H:%M.
      return pad(dt.getHours()) + ':' + pad(dt.getMinutes());
    }
    if (mode === 'datetime') {
      // dd/MM/yyyy hh:mm AM/PM; Django parsea %d/%m/%Y %I:%M %p.
      var h = dt.getHours();
      var meridiem = h >= 12 ? 'PM' : 'AM';
      var h12 = h % 12;
      if (h12 === 0) h12 = 12;
      return (
        dd + '/' + mm + '/' + yyyy + ' ' + h12 + ':' + pad(dt.getMinutes()) + ' ' + meridiem
      );
    }
    return dd + '/' + mm + '/' + yyyy;
  }

  function formatByMode(mode) {
    if (mode === 'time') {
      return 'HH:mm';
    }
    if (mode === 'datetime') {
      return 'dd/MM/yyyy hh:mm a';
    }
    return 'dd/MM/yyyy';
  }

  function buildOptions(mode) {
    var components = {
      calendar: false,
      date: false,
      month: false,
      year: false,
      decades: false,
      clock: false,
      hours: false,
      minutes: false,
      seconds: false,
    };
    var viewMode = 'calendar';
    if (mode === 'datetime') {
      components.calendar = true;
      components.date = true;
      components.month = true;
      components.year = true;
      components.decades = true;
      components.clock = true;
      components.hours = true;
      components.minutes = true;
    } else if (mode === 'time') {
      viewMode = 'clock';
      components.clock = true;
      components.hours = true;
      components.minutes = true;
    } else {
      viewMode = 'calendar';
      components.calendar = true;
      components.date = true;
      components.month = true;
      components.year = true;
      components.decades = true;
    }
    return {
      useCurrent: mode === 'date' ? false : true,
      promptTimeOnDateChange: mode === 'date' ? false : true,
      display: {
        viewMode: viewMode,
        components: components,
        theme: currentTheme(),
        icons: { type: 'icons', ...icons },
      },
      // Locale en/24h y formato explícito: locale-independiente; los formularios
      // parsean %H:%M, %d/%m/%Y %I:%M %p y %d/%m/%Y respectivamente.
      localization: { locale: 'en', format: formatByMode(mode) },
    };
  }

  // === Inicialización de pickers Tempus Dominus ===
  // Se crean UNA SOLA VEZ aquí, sobre los [data-tempus] presentes en DOMContentLoaded.
  // NO hay observer para nodos agregados después de la carga. Si en el futuro se
  // inyecta un [data-tempus] por JS (AJAX/htmx/fetch), inicializarlo con
  // initPicker(input) o añadir un MutationObserver que llame initPicker para cada
  // nodo nuevo — SIEMPRE con guarda anti-doble-init (ver abajo).
  function initPicker(input) {
    if (!input) return;
    if (window.tempusDominus && window.tempusDominus._instances && window.tempusDominus._instances[input.id]) {
      return; // ya inicializado: evita doble picker / doble suscripción
    }
    var pickerElement = input.parentElement;
    var mode = input.getAttribute('data-tempus') || 'date';
    // Backstop fiable: TD6 no siempre aplica localization por instancia, así
    // que forzamos el locale en DefaultOptions justo antes de crear el picker.
    // Hora en inglés (AM/PM) para que Django parsee %I:%M %p; fechas en español.
    try {
      var tdDef = window.tempusDominus.TempusDominus.DefaultOptions;
      if (tdDef && tdDef.localization) {
        tdDef.localization.locale = mode === 'time' ? 'en' : 'es';
      }
    } catch (e) {
      // Si DefaultOptions no es mutable, nos apoyamos en buildOptions.
    }
    var picker = new tempusDominus.TempusDominus(pickerElement, buildOptions(mode));
    window.tempusDominus._instances[input.id] = picker;
    picker.subscribe(tempusDominus.Namespace.events.change, function (e) {
      if (e.date) {
        input.value = canonicalFormat(e.date, mode);
      }
    });
    var trigger = pickerElement.querySelector('[data-tempus-trigger]');
    if (trigger) {
      trigger.addEventListener('click', function (e) {
        e.preventDefault();
        picker.toggle();
      });
    }
  }

  document.querySelectorAll('[data-tempus]').forEach(initPicker);

  var observer = new MutationObserver(function () {
    Object.keys(window.tempusDominus._instances).forEach(function (id) {
      var picker = window.tempusDominus._instances[id];
      picker.updateOptions({ display: { theme: currentTheme() } });
    });
  });
  observer.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['data-bs-theme'],
  });
});
