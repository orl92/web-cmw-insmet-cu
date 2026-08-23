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

  // e.date es un DateTime de Luxon (TD6), NO un Date de JS: usa .hour/.minute/etc.
  function canonicalFormat(date, mode) {
    var dd = pad(date.day);
    var mm = pad(date.month);
    var yyyy = date.year;
    var hours = date.hour;
    var meridiem = hours >= 12 ? 'PM' : 'AM';
    var hour12 = hours % 12;
    if (hour12 === 0) {
      hour12 = 12;
    }
    var hhmm12 = hour12 + ':' + pad(date.minute) + ' ' + meridiem;
    var hhmm24 = pad(hours) + ':' + pad(date.minute);
    if (mode === 'date') {
      return dd + '/' + mm + '/' + yyyy;
    }
    if (mode === 'time') {
      // 24h: locale-independiente, sin meridiano; Django parsea %H:%M.
      return hhmm24;
    }
    return dd + '/' + mm + '/' + yyyy + ' ' + hhmm12;
  }

  function formatByMode(mode) {
    if (mode === 'time') {
      // 24h: locale-independiente.
      return 'H:mm';
    }
    if (mode === 'datetime') {
      return 'dd/MM/yyyy h:mm a';
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
      localization:
        // Hora en 24h (HH:MM): locale-independiente; Django parsea %H:%M.
        mode === 'time'
          ? { locale: 'en', format: 'H:mm' }
          : { locale: 'es', format: formatByMode(mode) },
    };
  }

  document.querySelectorAll('[data-tempus]').forEach(function (input) {
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
  });

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
