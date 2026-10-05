(function () {
  'use strict';

  var SERVICE_ID = 'id_service';
  var LABEL_SELECTOR = '[data-period-quantity-label]';
  var NEUTRAL_LABEL = 'Cantidad';

  var PLURAL = { mes: 'meses', 'día': 'días' };

  function init() {
    var serviceSelect = document.getElementById(SERVICE_ID);
    var label = document.querySelector(LABEL_SELECTOR);
    if (!serviceSelect || !label) {
      return;
    }

    function update() {
      var option = serviceSelect.options[serviceSelect.selectedIndex];
      var unit = (option && option.dataset.periodUnit) || '';
      label.textContent = unit ? 'Cantidad de ' + (PLURAL[unit] || unit) : NEUTRAL_LABEL;
    }

    serviceSelect.addEventListener('change', update);
    update();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();