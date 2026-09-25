function showToast(message, type = 'danger', duration = 3000) {
    const Bootstrap = (window.tabler && window.tabler.bootstrap) || window.bootstrap;
    if (!Bootstrap || !Bootstrap.Toast) {
      console.error('showToast: Bootstrap no está disponible.');
      return;
    }
    const toastId = 'toast-' + Date.now();
    const safeMessage = String(message)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
    let icon, title;
    switch(type) {
      case 'success':
        icon = '<i class="icon ti ti-circle-check" style="--tblr-icon-size:24px"></i>';
        title = 'Éxito';
        break;
      case 'warning':
        icon = '<i class="icon ti ti-alert-triangle" style="--tblr-icon-size:24px"></i>';
        title = 'Advertencia';
        break;
      case 'info':
        icon = '<i class="icon ti ti-info-circle" style="--tblr-icon-size:24px"></i>';
        title = 'Información';
        break;
      default:
        icon = '<i class="icon ti ti-circle-x" style="--tblr-icon-size:24px"></i>';
        title = 'Error';
    }
    const toastHTML = `
      <div id="${toastId}" class="toast show" role="alert" aria-live="assertive" aria-atomic="true" data-bs-delay="${duration}">
        <div class="toast-header">
          <span class="me-2">${icon}</span>
          <strong class="me-auto">${title}</strong>
          <small class="text-muted">justo ahora</small>
          <button type="button" class="ms-2 btn-close" data-bs-dismiss="toast"></button>
        </div>
        <div class="toast-body">
          ${safeMessage}
        </div>
      </div>
    `;
    const toastContainer = document.getElementById('toast-container');
    if (toastContainer) {
      toastContainer.insertAdjacentHTML('beforeend', toastHTML);
      const toastElement = document.getElementById(toastId);
      const toast = new Bootstrap.Toast(toastElement, {
        delay: duration,
        autohide: true
      });
      toast.show();
      toastElement.addEventListener('hidden.bs.toast', function () {
        toastElement.remove();
      });
    }
  }
  function initAutoDismissAlerts() {
    document.querySelectorAll('.alert.alert-dismissible').forEach(alert => {
      setTimeout(() => {
        const closeButton = alert.querySelector('.btn-close');
        if (closeButton) {
          closeButton.click();
        }
      }, 5000);
    });
  }
  function clearValidation(field) {
    field.classList.remove('is-valid', 'is-invalid');
  }
  function markAsValid(field) {
    field.classList.add('is-valid');
    field.classList.remove('is-invalid');
  }
  function markAsInvalid(field) {
    field.classList.add('is-invalid');
    field.classList.remove('is-valid');
  }
  function validateRequired(field) {
    const value = field.value.trim();
    if (field.hasAttribute('required') && !value) {
      markAsInvalid(field);
      return false;
    }
    return true;
  }
  function initPasswordToggles() {
    document.querySelectorAll('.password-toggle').forEach(toggle => {
      toggle.addEventListener('click', function() {
        const input = this.closest('.input-group').querySelector('input');
        const icon = this.querySelector('i');
        if (input.type === 'password') {
          input.type = 'text';
          icon.classList.remove('ti-eye');
          icon.classList.add('ti-eye-off');
        } else {
          input.type = 'password';
          icon.classList.remove('ti-eye-off');
          icon.classList.add('ti-eye');
        }
      });
    });
  }
  document.addEventListener('DOMContentLoaded', function() {
    initPasswordToggles();
    initAutoDismissAlerts();
  });
