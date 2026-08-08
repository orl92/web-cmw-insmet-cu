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

  function currentTheme() {
    return document.documentElement.getAttribute('data-bs-theme') === 'dark'
      ? 'dark'
      : 'light';
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
    var format = 'yyyy-MM-dd';
    if (mode === 'datetime') {
      components.calendar = true;
      components.date = true;
      components.month = true;
      components.year = true;
      components.decades = true;
      components.clock = true;
      components.hours = true;
      components.minutes = true;
      format = "yyyy-MM-dd'T'HH:mm";
    } else if (mode === 'time') {
      viewMode = 'clock';
      components.clock = true;
      components.hours = true;
      components.minutes = true;
      format = 'HH:mm';
    } else {
      components.calendar = true;
      components.date = true;
      components.month = true;
      components.year = true;
      components.decades = true;
    }
    return {
      display: {
        viewMode: viewMode,
        components: components,
        theme: currentTheme(),
        icons: { type: 'icons', ...icons },
      },
      localization: { locale: 'es', format: format },
    };
  }

  document.querySelectorAll('[data-tempus]').forEach(function (input) {
    var pickerElement = input.parentElement;
    var mode = input.getAttribute('data-tempus') || 'date';
    var picker = new tempusDominus.TempusDominus(pickerElement, buildOptions(mode));
    window.tempusDominus._instances[input.id] = picker;
    picker.subscribe(tempusDominus.Namespace.events.change, function (e) {
      if (e.date) {
        input.value = picker.dates.picked[0].format(picker.options.localization.format);
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
