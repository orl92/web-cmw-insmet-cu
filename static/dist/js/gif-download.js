// gif-download.js
// Manejo del modal de descarga de GIF animado

class GifDownloadManager {
    constructor(config) {
        this.config = config;
        this.modal = null;
        this.confirmBtn = null;
        this.clearBtn = null;
        this.downloadStatus = null;
        this.statusMessage = null;
        this.successToast = null;

        this.init();
    }

    init() {
        this.modal = document.getElementById('gifModal');
        this.confirmBtn = document.getElementById('confirmDownloadGif');
        this.clearBtn = document.getElementById('clearGifForm');
        this.downloadStatus = document.getElementById('download-status');
        this.statusMessage = document.getElementById('status-message');
        this.successToast = new bootstrap.Toast(document.getElementById('successToast'));

        if (!this.validateElements()) {
            console.error('No se pudieron inicializar todos los elementos del modal de GIF');
            return;
        }

        this.setupEventListeners();
    }

    validateElements() {
        const requiredElements = [
            this.modal, this.confirmBtn, this.clearBtn,
            this.downloadStatus, this.statusMessage
        ];

        return requiredElements.every(element => element !== null);
    }

    setupEventListeners() {
        // Evento cuando se abre el modal
        this.modal.addEventListener('show.bs.modal', () => {
            this.hideDownloadStatus();
            this.updateModalFormValues();
        });

        // Evento cuando se cierra el modal
        this.modal.addEventListener('hidden.bs.modal', () => {
            this.hideDownloadStatus();
        });

        // Eventos para cambios en los campos principales
        this.setupMainFormListeners();

        // Evento para el botón de descarga
        this.confirmBtn.addEventListener('click', () => {
            this.handleDownload();
        });

        // Evento para el botón de limpiar
        this.clearBtn.addEventListener('click', () => {
            this.clearForm();
        });
    }

    setupMainFormListeners() {
        const mainFields = ['datepicker', 'hour-select', 'id_var_name'];

        mainFields.forEach(fieldId => {
            const field = document.getElementById(fieldId);
            if (field) {
                field.addEventListener('change', () => {
                    if (this.modal && this.modal.classList.contains('show')) {
                        this.updateModalFormValues();
                    }
                });
            }
        });
    }

    updateModalFormValues() {
        const dateValue = document.getElementById('datepicker').value;
        const hourValue = document.getElementById('hour-select').value;
        const varNameValue = document.getElementById('id_var_name').value;

        // Formatear datetime_init
        const formattedDate = dateValue.replace(/-/g, '');
        const datetimeInit = formattedDate + hourValue;

        // Actualizar campos ocultos
        document.getElementById('gif_datetime_init').value = datetimeInit;
        document.getElementById('gif_var_name').value = varNameValue;

        // Establecer valores por defecto si están vacíos
        this.setDefaultDateValues(datetimeInit);
    }

    setDefaultDateValues(datetimeInit) {
        const fechaInicioField = document.getElementById(this.config.fechaInicioId);
        const fechaFinField = document.getElementById(this.config.fechaFinId);

        if (fechaInicioField && !fechaInicioField.value) {
            fechaInicioField.value = datetimeInit;
        }

        if (fechaFinField && !fechaFinField.value) {
            const fechaFin = this.calculateDefaultEndDate(datetimeInit);
            fechaFinField.value = fechaFin;
        }
    }

    calculateDefaultEndDate(datetimeInit) {
        const fechaInicioObj = new Date(
            parseInt(datetimeInit.substring(0, 4)),
            parseInt(datetimeInit.substring(4, 6)) - 1,
            parseInt(datetimeInit.substring(6, 8)),
            parseInt(datetimeInit.substring(8, 10))
        );

        const fechaFinObj = new Date(fechaInicioObj.getTime() + (18 * 60 * 60 * 1000)); // +18 horas

        const year = fechaFinObj.getFullYear();
        const month = String(fechaFinObj.getMonth() + 1).padStart(2, '0');
        const day = String(fechaFinObj.getDate()).padStart(2, '0');
        const hours = String(fechaFinObj.getHours()).padStart(2, '0');

        return `${year}${month}${day}${hours}`;
    }

    clearForm() {
        const fechaInicioField = document.getElementById(this.config.fechaInicioId);
        const fechaFinField = document.getElementById(this.config.fechaFinId);

        if (fechaInicioField) fechaInicioField.value = '';
        if (fechaFinField) fechaFinField.value = '';

        this.hideDownloadStatus();
        this.updateModalFormValues();
    }

    showDownloadStatus(message, isError = false) {
        if (!this.downloadStatus || !this.statusMessage) return;

        this.statusMessage.textContent = message;
        this.downloadStatus.classList.remove('d-none', 'alert-danger', 'alert-success');
        this.downloadStatus.classList.add(isError ? 'alert-danger' : 'alert-info');

        const spinner = this.downloadStatus.querySelector('.spinner-border');
        if (spinner) {
            spinner.classList.toggle('d-none', isError);
        }
    }

    hideDownloadStatus() {
        if (this.downloadStatus) {
            this.downloadStatus.classList.add('d-none');
        }
    }

    showSuccessNotification(message) {
        const toastMessage = document.getElementById('toast-message');
        if (toastMessage) {
            toastMessage.textContent = message;
        }
        if (this.successToast) {
            this.successToast.show();
        }
    }

    async handleDownload() {
        const formData = this.getFormData();

        if (!this.validateFormData(formData)) {
            return;
        }

        if (!this.validateDateRange(formData)) {
            return;
        }

        await this.processDownload(formData);
    }

    getFormData() {
        return {
            datetimeInit: document.getElementById('gif_datetime_init').value,
            varName: document.getElementById('gif_var_name').value,
            fechaInicio: document.getElementById(this.config.fechaInicioId).value,
            fechaFin: document.getElementById(this.config.fechaFinId).value
        };
    }

    validateFormData(data) {
        const { datetimeInit, varName, fechaInicio, fechaFin } = data;

        if (!datetimeInit || !varName || !fechaInicio || !fechaFin) {
            this.showDownloadStatus('Por favor, complete todos los campos requeridos.', true);
            return false;
        }

        const dateRegex = /^\d{10}$/;
        if (!dateRegex.test(fechaInicio) || !dateRegex.test(fechaFin)) {
            this.showDownloadStatus('Las fechas deben tener el formato YYYYMMDDHH (10 dígitos).', true);
            return false;
        }

        if (parseInt(fechaInicio) > parseInt(fechaFin)) {
            this.showDownloadStatus('La fecha de inicio no puede ser mayor que la fecha final.', true);
            return false;
        }

        return true;
    }

    validateDateRange(data) {
        const { fechaInicio, fechaFin } = data;

        const fechaInicioObj = new Date(
            parseInt(fechaInicio.substring(0, 4)),
            parseInt(fechaInicio.substring(4, 6)) - 1,
            parseInt(fechaInicio.substring(6, 8)),
            parseInt(fechaInicio.substring(8, 10))
        );

        const fechaFinObj = new Date(
            parseInt(fechaFin.substring(0, 4)),
            parseInt(fechaFin.substring(4, 6)) - 1,
            parseInt(fechaFin.substring(6, 8)),
            parseInt(fechaFin.substring(8, 10))
        );

        const diferenciaHoras = (fechaFinObj - fechaInicioObj) / (1000 * 60 * 60);
        if (diferenciaHoras > 72) {
            this.showDownloadStatus('El rango máximo permitido es de 3 días (72 horas).', true);
            return false;
        }

        return true;
    }

    async processDownload(data) {
        this.showDownloadStatus('Generando GIF animado, por favor espere...');
        this.confirmBtn.disabled = true;

        try {
            const downloadUrl = this.buildDownloadUrl(data);
            await this.downloadGif(downloadUrl, data);

            this.hideDownloadStatus();
            this.showSuccessNotification('¡GIF descargado exitosamente!');

        } catch (error) {
            this.handleDownloadError(error);
        } finally {
            setTimeout(() => {
                this.confirmBtn.disabled = false;
            }, 1000);
        }
    }

    buildDownloadUrl(data) {
        const params = new URLSearchParams({
            'datetime_init': data.datetimeInit,
            'var_name': data.varName,
            'fecha_inicio': data.fechaInicio,
            'fecha_fin': data.fechaFin
        });

        return `${this.config.downloadUrl}?${params.toString()}`;
    }

    async downloadGif(downloadUrl, data) {
        const response = await fetch(downloadUrl);

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(errorText || `Error ${response.status}: ${response.statusText}`);
        }

        const blob = await response.blob();

        if (blob.size === 0) {
            throw new Error('El archivo GIF está vacío');
        }

        // Crear enlace temporal para descarga
        const link = document.createElement('a');
        const url = window.URL.createObjectURL(blob);
        link.href = url;
        link.download = `${data.varName}_${data.fechaInicio}_to_${data.fechaFin}.gif`;
        document.body.appendChild(link);
        link.click();

        // Limpiar
        window.URL.revokeObjectURL(url);
        document.body.removeChild(link);
    }

    handleDownloadError(error) {
        console.error('Error en la descarga:', error);

        let errorMessage = 'Error al descargar el GIF';
        if (error.message.includes('No se encontraron imágenes')) {
            errorMessage = 'No se encontraron imágenes para el rango seleccionado';
        } else if (error.message.includes('rango máximo')) {
            errorMessage = 'El rango seleccionado excede el límite permitido';
        } else if (error.message.includes('conexión') || error.message.includes('timeout')) {
            errorMessage = 'Error de conexión con el servidor';
        } else if (error.message.includes('No se pudieron cargar imágenes')) {
            errorMessage = 'No se pudieron cargar las imágenes para generar el GIF';
        }

        this.showDownloadStatus(errorMessage, true);
    }
}

// Inicialización cuando el DOM está listo
document.addEventListener('DOMContentLoaded', function() {
    if (window.GIF_DOWNLOAD_CONFIG) {
        new GifDownloadManager(window.GIF_DOWNLOAD_CONFIG);
    } else {
        console.warn('Configuración de GIF download no encontrada');
    }
});