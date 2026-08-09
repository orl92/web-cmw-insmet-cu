// Clase principal para manejar la visualización de imágenes meteorológicas
class MeteoPlotter {
    constructor(params) {
        // Configuración inicial
        this.datetimeInit = params.datetimeInit;
        this.varName = params.varName;
        this.varLabel = params.varLabel;
        this.imageUrls = params.imageUrls || [];
        this.simulationDate = params.simulationDate;
        this.count = params.count;

        // Elementos del DOM
        this.galleryContainer = document.getElementById('gallery-container');
        this.emptyStateElement = document.getElementById('empty-state');
        this.errorContainer = document.getElementById('error-container');
        this.errorMessageElement = document.getElementById('error-message');

        // Para auto-ocultar errores
        this.autoHideTimeout = null;
    }

    showError(message) {
        if (!this.errorContainer || !this.errorMessageElement) return;

        // Limpiar timeout anterior si existe
        if (this.autoHideTimeout) {
            clearTimeout(this.autoHideTimeout);
        }

        this.errorMessageElement.textContent = message;
        this.errorContainer.classList.remove('d-none');
        this.errorContainer.classList.add('show');

        // Auto-ocultar después de 5 segundos
        this.autoHideTimeout = setTimeout(() => {
            this.hideError();
        }, 5000);
    }

    hideError() {
        if (this.errorContainer) {
            this.errorContainer.classList.remove('show');
            setTimeout(() => {
                this.errorContainer.classList.add('d-none');
            }, 150);
        }
    }

    showEmptyState() {
        this.hideError();
        if (this.emptyStateElement) {
            this.emptyStateElement.classList.remove('d-none');
        }

        if (this.galleryContainer) {
            this.galleryContainer.innerHTML = '';
        }
    }

    createImageGallery() {
        if (!this.galleryContainer) return;

        this.galleryContainer.innerHTML = '';
        this.hideError();

        // Ocultar estado vacío
        if (this.emptyStateElement) {
            this.emptyStateElement.classList.add('d-none');
        }

        if (this.imageUrls.length === 0) {
            this.showEmptyState();
            return;
        }

        this.imageUrls.forEach((url, index) => {
            const col = document.createElement('div');
            col.className = 'col-lg-4';

            // Extraer nombre del archivo para el título
            const filename = url.split('/').pop();
            const timePart = filename.split('_').pop().replace('.png', '').replace('T', ' ').replace(/-/g, ':');

            // Usar el proxy para evitar problemas de CORS
            const imagePath = url.replace('http://imgwrfserver.cmw.insmet.cu', '');
            const proxyUrl = `/proxy_image_modelo/?image_path=${encodeURIComponent(imagePath)}`;

            col.innerHTML = `
                <div class="row g-2 g-md-3">
                    <div class="col-12">
                        <a data-fslightbox="gallery" href="${proxyUrl}" data-caption="${this.varLabel} - ${timePart}">
                            <div class="img-responsive img-responsive-3x1 rounded-3 border"
                                 style="background-image: url(${proxyUrl})">
                            </div>
                        </a>
                        <figcaption class="figure-caption text-center">${timePart}</figcaption>
                    </div>
                </div>
            `;

            this.galleryContainer.appendChild(col);
        });

        // Inicializar FS Lightbox después de un breve delay
        setTimeout(() => {
            if (typeof refreshFsLightbox === 'function') {
                refreshFsLightbox();
            }
        }, 100);
    }

    cleanupGallery() {
        this.hideError();

        if (this.galleryContainer) {
            this.galleryContainer.innerHTML = '';
        }

        // Ocultar estado vacío
        if (this.emptyStateElement) {
            this.emptyStateElement.classList.add('d-none');
        }
    }

    init() {
        try {
            this.cleanupGallery();
            this.createImageGallery();
        } catch (error) {
            console.error('Error en MeteoPlotter:', error);
            this.showError(this.cleanErrorDisplay(error.message));
        }
    }

    // Método para limpiar la visualización de errores
    cleanErrorDisplay(errorMessage) {
        try {
            if (typeof errorMessage === 'string' && errorMessage.includes('{')) {
                const errorObj = JSON.parse(errorMessage);
                return errorObj.message || errorMessage;
            }
            return errorMessage;
        } catch (e) {
            return errorMessage;
        }
    }
}

// Función para asignar la fecha por defecto (picker lo gestiona Tempus Dominus via data-tempus)
function initDatepickerDefault() {
    const today = new Date();

    const datepickerElement = document.getElementById('datepicker');
    if (datepickerElement && !datepickerElement.value) {
        datepickerElement.value = window.formatPickerDate
            ? window.formatPickerDate(today)
            : today.toISOString().split('T')[0];
    }
}

// Función para enviar el formulario automáticamente
async function submitFormWithDefaultValues() {
    const form = document.getElementById('data-form');
    const plotArea = document.getElementById('plot-area');
    const plotTitle = document.getElementById('plot-title');
    const galleryContainer = document.getElementById('gallery-container');
    const errorContainer = document.getElementById('error-container');

    if (!form) return;

    // Ocultar error previo
    if (errorContainer) {
        errorContainer.classList.add('d-none');
    }

    // Ocultar galería y mostrar área de plot
    if (galleryContainer) galleryContainer.innerHTML = '';
    if (plotArea) plotArea.style.display = 'block';

    // Construir datetime_init a partir de los campos de fecha y hora
    const dateValue = document.getElementById('datepicker').value;
    const hourValue = document.getElementById('hour-select').value;
    const formattedDate = window.pickerDateToId
        ? window.pickerDateToId(dateValue)
        : dateValue.replace(/-/g, '');
    const datetimeInit = formattedDate + hourValue;

    const formData = {
        datetime_init: datetimeInit,
        var_name: form.var_name.value,
        csrfmiddlewaretoken: document.querySelector('[name=csrfmiddlewaretoken]').value
    };

    try {
        const response = await fetch('', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': formData.csrfmiddlewaretoken
            },
            body: JSON.stringify(formData)
        });

        const data = await response.json();

        if (!response.ok || data.status !== 'success') {
            throw new Error(data.message || `Error ${response.status}: ${response.statusText}`);
        }

        if (plotTitle) plotTitle.textContent = `${data.var_label} - ${data.datetime_init}`;

        const plotter = new MeteoPlotter({
            datetimeInit: data.datetime_init,
            varName: data.var_name,
            varLabel: data.var_label,
            imageUrls: data.image_urls,
            simulationDate: data.simulation_date,
            count: data.count
        });

        plotter.init();

    } catch (error) {
        console.error('Error:', error);

        // Mostrar error usando el método de MeteoPlotter
        const plotter = new MeteoPlotter({ imageUrls: [] });
        plotter.showError(error.message);
    }
}

// Función para formatear errores de forma más amigable
function formatErrorMessage(error) {
    if (!error) return 'Error desconocido';

    const errorStr = error.toString();

    // Manejar errores comunes de la API
    if (errorStr.includes('404')) {
        return 'No se encontraron datos para los parámetros seleccionados. Por favor, intente con otra fecha o variable.';
    } else if (errorStr.includes('Network Error') || errorStr.includes('Failed to fetch')) {
        return 'Error de conexión. Por favor, verifique su conexión a internet e intente nuevamente.';
    } else if (errorStr.includes('Timeout')) {
        return 'La solicitud tardó demasiado tiempo. Por favor, intente nuevamente.';
    } else if (errorStr.includes('500')) {
        return 'Error interno del servidor. Por favor, contacte al administrador.';
    }

    // Para otros errores, devolver el mensaje original pero limpiado
    return errorStr.replace(/Error:|["{}]/g, '').trim();
}

// Código de inicialización cuando el DOM está listo
document.addEventListener('DOMContentLoaded', function () {
    // Inicializar fecha por defecto
    initDatepickerDefault();

    const form = document.getElementById('data-form');

    // Enviar formulario automáticamente al cargar la página
    setTimeout(() => {
        submitFormWithDefaultValues();
    }, 500);

    if (form) {
        form.addEventListener('submit', async function (e) {
            e.preventDefault();

            if (!form.checkValidity()) {
                e.stopPropagation();
                form.classList.add('was-validated');
                return;
            }

            await submitFormWithDefaultValues();
        });
    }
});


// Función para mostrar notificaciones toast (opcional)
function showToast(message, type = 'info') {
    // Si no existe el contenedor de toasts, crearlo
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }

    const toastId = 'toast-' + Date.now();
    const bgClass = type === 'success' ? 'bg-success' : type === 'error' ? 'bg-danger' : 'bg-info';

    const toastHTML = `
        <div id="${toastId}" class="toast ${bgClass} text-white" role="alert">
            <div class="toast-body">
                <div class="d-flex align-items-center">
                    <i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle'} me-2"></i>
                    <span>${message}</span>
                    <button type="button" class="btn-close btn-close-white ms-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
            </div>
        </div>
    `;

    toastContainer.insertAdjacentHTML('beforeend', toastHTML);

    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement);
    toast.show();

    // Remover el toast del DOM después de que se oculte
    toastElement.addEventListener('hidden.bs.toast', function() {
        toastElement.remove();
    });
}

// Para depuración
window.MeteoPlotter = MeteoPlotter;
window.submitFormWithDefaultValues = submitFormWithDefaultValues;
