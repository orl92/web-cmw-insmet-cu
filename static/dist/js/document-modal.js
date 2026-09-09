document.addEventListener('DOMContentLoaded', function () {
  var modal = document.getElementById('documentPdfModal');
  if (!modal) return;
  modal.addEventListener('show.bs.modal', function (e) {
    var trigger = e.relatedTarget;
    if (!trigger) return;
    var url = trigger.getAttribute('data-pdf-url');
    var title = trigger.getAttribute('data-pdf-title') || 'Documento';
    var obj = document.getElementById('documentPdfObject');
    var download = document.getElementById('documentPdfDownload');
    document.getElementById('documentPdfModalLabel').textContent = title;
    if (download) download.href = url;
    if (obj && obj.getAttribute('data') !== url) obj.setAttribute('data', url); // no double-fetch
  });
  modal.addEventListener('hidden.bs.modal', function () {
    var obj = document.getElementById('documentPdfObject');
    var download = document.getElementById('documentPdfDownload');
    if (obj) obj.setAttribute('data', '');
    if (download) download.href = '';
  });
});

// Inicializar tooltips en los botones que abren el modal PDF (#documentPdfModal)
// y muestran SOLO un icono (btn-icon, típicamente en listados).
// Los botones de los campos de formulario ya muestran el texto "Ver PDF",
// por lo que un tooltip sería redundante.
// Estos botones llevan data-bs-toggle="modal", por lo que el data-api de tooltips
// (selector [data-bs-toggle="tooltip"]) no los inicializa; lo hacemos manualmente.
document.addEventListener('DOMContentLoaded', function () {
  var pdfTriggers = document.querySelectorAll('[data-pdf-url].btn-icon');
  if (!pdfTriggers.length) return;
  var Bs = (window.tabler && window.tabler.bootstrap) || window.bootstrap;
  if (!Bs || !Bs.Tooltip) return;
  pdfTriggers.forEach(function (el) {
    if (Bs.Tooltip.getInstance(el)) return;
    var title =
      el.getAttribute('data-bs-original-title') ||
      el.getAttribute('aria-label') ||
      'Ver PDF';
    new Bs.Tooltip(el, { title: title });
  });
});
