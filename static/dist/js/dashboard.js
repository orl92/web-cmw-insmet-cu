document.addEventListener("DOMContentLoaded", function () {
  var currentTheme = document.documentElement.getAttribute('data-bs-theme') || 'light';

  // ===== GRÁFICO: TEMPERATURA =====
  var tempChartEl = document.getElementById("temperatureTrendChart");
  if (tempChartEl) {
    var days = JSON.parse(tempChartEl.dataset.labels);
    new ApexCharts(tempChartEl, {
      chart: {
        type: "line",
        fontFamily: "inherit",
        height: 320,
        parentHeightOffset: 0,
        toolbar: { show: false },
        animations: { enabled: false }
      },
      stroke: { width: 2, lineCap: "round", curve: "smooth" },
      series: [
        { name: "Costa Norte Máx", data: JSON.parse(tempChartEl.dataset.seriesNorthMax) },
        { name: "Costa Norte Mín", data: JSON.parse(tempChartEl.dataset.seriesNorthMin) },
        { name: "Interior Máx", data: JSON.parse(tempChartEl.dataset.seriesInlandMax) },
        { name: "Interior Mín", data: JSON.parse(tempChartEl.dataset.seriesInlandMin) },
        { name: "Costa Sur Máx", data: JSON.parse(tempChartEl.dataset.seriesSouthMax) },
        { name: "Costa Sur Mín", data: JSON.parse(tempChartEl.dataset.seriesSouthMin) }
      ],
      tooltip: {
        theme: currentTheme,
        fillSeriesColor: false,
        y: { formatter: function (value) { return value + "°C"; } }
      },
      grid: {
        padding: { top: -20, right: 0, left: -4, bottom: -4 },
        strokeDashArray: 4,
        borderColor: 'transparent'
      },
      dataLabels: { enabled: true },
      xaxis: {
        categories: days,
        labels: {
          padding: 0,
          style: { colors: 'var(--tblr-body-color)', fontSize: '12px', fontFamily: 'inherit' }
        },
        tooltip: { enabled: false },
        axisBorder: { show: false },
        axisTicks: { show: false }
      },
      yaxis: {
        labels: {
          padding: 4,
          style: { colors: 'var(--tblr-body-color)', fontSize: '12px', fontFamily: 'inherit' },
          formatter: function (val) { return val + "°"; }
        },
        axisBorder: { show: false }
      },
      colors: [
        "var(--chart-temperature-color-0)",
        "var(--chart-temperature-color-1)",
        "var(--chart-temperature-color-2)",
        "var(--chart-temperature-color-3)",
        "var(--chart-temperature-color-4)",
        "var(--chart-temperature-color-5)"
      ],
      legend: {
        show: true,
        position: "bottom",
        offsetY: 12,
        markers: { width: 10, height: 10, radius: 100 },
        itemMargin: { horizontal: 8, vertical: 8 },
        labels: {
          colors: 'var(--tblr-body-color)',
          useSeriesColors: false,
          style: { fontSize: '13px', fontFamily: 'inherit', fontWeight: 400 }
        }
      },
      markers: { size: 2, hover: { size: 6 } }
    }).render();
  }

  // ===== GRÁFICO: INGRESOS MENSUALES =====
  var incomeChartEl = document.getElementById("incomeChart");
  if (incomeChartEl) {
    new ApexCharts(incomeChartEl, {
      chart: {
        type: "bar",
        fontFamily: "inherit",
        height: 320,
        parentHeightOffset: 0,
        toolbar: { show: false },
        animations: { enabled: false }
      },
      stroke: { width: 2, lineCap: "round" },
      series: [
        { name: "Facturado", data: JSON.parse(incomeChartEl.dataset.billed) },
        { name: "Pagado", data: JSON.parse(incomeChartEl.dataset.paid) }
      ],
      tooltip: {
        theme: currentTheme,
        y: {
          formatter: function (value) {
            return value.toLocaleString('es-CU', { style: 'currency', currency: 'CUP', minimumFractionDigits: 0 });
          }
        }
      },
      grid: {
        padding: { top: -20, right: 0, left: -4, bottom: -4 },
        strokeDashArray: 4,
        borderColor: 'transparent'
      },
      dataLabels: { enabled: false },
      xaxis: {
        categories: JSON.parse(incomeChartEl.dataset.months),
        labels: {
          padding: 0,
          style: { colors: 'var(--tblr-body-color)', fontSize: '12px', fontFamily: 'inherit' }
        },
        tooltip: { enabled: false },
        axisBorder: { show: false },
        axisTicks: { show: false }
      },
      yaxis: {
        labels: {
          padding: 4,
          style: { colors: 'var(--tblr-body-color)', fontSize: '12px', fontFamily: 'inherit' },
          formatter: function (val) {
            return val.toLocaleString('es-CU', { style: 'currency', currency: 'CUP', minimumFractionDigits: 0 });
          }
        },
        axisBorder: { show: false }
      },
      colors: ["#206bc4", "#2fb344"],
      plotOptions: {
        bar: { borderRadius: 4, columnWidth: '60%' }
      },
      legend: {
        show: true,
        position: "top",
        fontFamily: "inherit",
        labels: { colors: "var(--tblr-body-color)" },
        markers: { width: 8, height: 8, radius: 2 }
      }
    }).render();
  }

  // ===== GRÁFICO: SUSCRIPCIONES =====
  var subsChartEl = document.getElementById("subscriptionsChart");
  if (subsChartEl) {
    var activeSubs = parseInt(subsChartEl.dataset.active);
    var pendingSubs = parseInt(subsChartEl.dataset.pending);
    var expiredSubs = parseInt(subsChartEl.dataset.expired);
    var requestedSubs = parseInt(subsChartEl.dataset.requested);
    var totalSubs = activeSubs + pendingSubs + expiredSubs + requestedSubs;
    var subsData = {
      active: { label: 'Activas', list: JSON.parse(subsChartEl.dataset.activeList) },
      pending: { label: 'Pendientes', list: JSON.parse(subsChartEl.dataset.pendingList) },
      expired: { label: 'Vencidas', list: JSON.parse(subsChartEl.dataset.expiredList) },
      requested: { label: 'Solicitadas', list: JSON.parse(subsChartEl.dataset.requestedList) }
    };
    var subsCategories = ['active', 'pending', 'expired', 'requested'];

    function escapeHtml(str) {
      return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
    }

    function buildSubsTable(category) {
      var data = subsData[category];
      if (!data.list.length) {
        return '<div class="text-center text-muted py-5">No hay suscripciones en esta categoría</div>';
      }
      var html = '<div class="table-responsive"><table class="table table-sm table-hover table-vcenter table-bordered mb-0"><thead><tr><th>Cliente</th><th>Servicio</th><th>Vencimiento</th></tr></thead><tbody>';
      for (var i = 0; i < data.list.length; i++) {
        var s = data.list[i];
        html += '<tr><td>' + escapeHtml(s.customer) + '</td><td>' + escapeHtml(s.service) + '</td><td>' + s.end_date + '</td></tr>';
      }
      html += '</tbody></table></div>';
      return html;
    }

    new ApexCharts(subsChartEl, {
      chart: {
        type: "donut",
        fontFamily: "inherit",
        height: 320,
        parentHeightOffset: 0,
        toolbar: { show: false },
        animations: { enabled: false },
        events: {
          dataPointSelection: function (event, chartContext, config) {
            var category = subsCategories[config.dataPointIndex];
            var data = subsData[category];
            document.getElementById('subscriptionsModalLabel').textContent = 'Suscripciones ' + data.label;
            document.getElementById('subscriptionsModalContent').innerHTML = buildSubsTable(category);
            var modal = new window.tabler.Modal(document.getElementById('subscriptionsModal'));
            modal.show();
          }
        }
      },
      series: [activeSubs, pendingSubs, expiredSubs, requestedSubs],
      labels: ["Activas", "Pendientes", "Vencidas", "Solicitadas"],
      colors: ["#2fb344", "#f59f00", "#d63939", "#17a2b8"],
      stroke: { width: 2 },
      plotOptions: {
        pie: {
          expandOnClick: true,
          donut: {
            size: "65%",
            labels: {
              show: true,
              total: {
                show: true,
                label: "Total",
                fontSize: "14px",
                fontFamily: "inherit",
                formatter: function () { return totalSubs; }
              }
            }
          }
        }
      },
      dataLabels: {
        enabled: true,
        style: { fontSize: "12px", fontFamily: "inherit" },
        formatter: function (val, opts) {
          return opts.w.config.series[opts.seriesIndex] + " (" + val.toFixed(1) + "%)";
        }
      },
      tooltip: {
        theme: currentTheme,
        y: {
          formatter: function (val) {
            return val + " suscripción" + (val !== 1 ? "es" : "");
          }
        }
      },
      legend: {
        show: true,
        position: "bottom",
        fontFamily: "inherit",
        labels: { colors: "var(--tblr-body-color)" },
        formatter: function (label, opts) {
          return label + ": " + opts.w.globals.series[opts.seriesIndex];
        }
      },
      responsive: [
        { breakpoint: 480, options: { chart: { height: 260 }, legend: { position: "bottom" } } }
      ]
    }).render();
  }
});
