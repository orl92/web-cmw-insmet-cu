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
