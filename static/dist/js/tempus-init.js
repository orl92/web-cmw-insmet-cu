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

  function canonicalFormat(date, mode) {
    var dd = pad(date.getDate());
    var mm = pad(date.getMonth() + 1);
    var yyyy = date.getFullYear();
    var hours = date.getHours();
    var meridiem = hours >= 12 ? 'PM' : 'AM';
    var hour12 = hours % 12;
    if (hour12 === 0) {
      hour12 = 12;
    }
    var hhmm = hour12 + ':' + pad(date.getMinutes()) + ' ' + meridiem;
    if (mode === 'date') {
      return dd + '/' + mm + '/' + yyyy;
    }
    if (mode === 'time') {
      return hhmm;
    }
    return dd + '/' + mm + '/' + yyyy + ' ' + hhmm;
  }

  function formatByMode(mode) {
    if (mode === 'time') {
      return 'h:mm a';
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
      localization: { locale: 'es', format: formatByMode(mode) },
    };
  }

  document.querySelectorAll('[data-tempus]').forEach(function (input) {
    var pickerElement = input.parentElement;
    var mode = input.getAttribute('data-tempus') || 'date';
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
