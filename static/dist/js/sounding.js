// static/dist/js/sounding-form.js
class SoundingFormHandler {
    constructor() {
        this.initElements();
        this.bindEvents();
        this.initLitepicker();
        this.setupDatetimeHandlers();
        this.setupTownChangeHandler();
        this.initForecastSelect();
        this.checkUrlParams();
    }

    initElements() {
        this.form = document.getElementById('sounding-form');
        this.submitBtn = this.form.querySelector('button[type="submit"]');
        this.loadingEl = document.getElementById('loading');
        this.plotEl = document.getElementById('sounding-plot');
        this.emptyPlotEl = document.getElementById('empty-plot');
        this.datetimeInfoEl = document.getElementById('datetime-info');
        this.paramsInfoEl = document.getElementById('params-info');
        this.datePicker = document.getElementById('datepicker');
        this.hourSelect = document.getElementById('hour-select');
        this.forecastSelect = document.getElementById('forecast-select');
        this.datetimeInitEl = document.getElementById('datetime-init');
        this.townSelect = document.getElementById('id_town');
    }

    bindEvents() {
        this.form.addEventListener('submit', (e) => this.handleSubmit(e));
    }

    initLitepicker() {
        if (this.datePicker) {
            // Destruir cualquier instancia previa de Litepicker
            if (this.datePicker._litepicker) {
                this.datePicker._litepicker.destroy();
            }
            
            new Litepicker({
                element: this.datePicker,
                format: 'YYYY-MM-DD',
                lang: 'es-ES',
                resetButton: false,
                buttonText: {
                    previousMonth: `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon icon-1"><path d="M15 6l-6 6l6 6" /></svg>`,
                    nextMonth: `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon icon-1"><path d="M9 6l6 6l-6 6" /></svg>`
                }
            });
        }
    }

    setupDatetimeHandlers() {
        if (this.datePicker) {
            this.datePicker.addEventListener('change', () => {
                this.updateDatetimeInit();
                this.updateForecastOptions();
            });
        }
        
        if (this.hourSelect) {
            this.hourSelect.addEventListener('change', () => {
                this.updateDatetimeInit();
                this.updateForecastOptions();
            });
        }
    }

    setupTownChangeHandler() {
        if (this.townSelect) {
            this.townSelect.addEventListener('change', (e) => {
                const selectedOption = e.target.options[e.target.selectedIndex];
                const lat = selectedOption.getAttribute('data-lat');
                const long = selectedOption.getAttribute('data-long');
                
                // Actualizar campos ocultos si existen
                if (document.querySelector('[name="lat"]')) {
                    document.querySelector('[name="lat"]').value = lat;
                }
                if (document.querySelector('[name="long"]')) {
                    document.querySelector('[name="long"]').value = long;
                }
            });
        }
    }

    updateDatetimeInit() {
        const dateValue = this.datePicker.value;
        const hourValue = this.hourSelect.value;
        const formattedDate = dateValue.replace(/-/g, '') + hourValue;
        this.datetimeInitEl.value = formattedDate;
    }

    initForecastSelect() {
        this.weekdays = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'];
        this.months = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
                       'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'];
        this.updateForecastOptions();
    }

    updateForecastOptions() {
        if (!this.datePicker || !this.hourSelect || !this.forecastSelect) return;
        
        const dateValue = this.datePicker.value;
        const hourValue = this.hourSelect.value;
        
        if (!dateValue || !hourValue) return;
        
        const baseDate = new Date(`${dateValue}T${hourValue}:00Z`);
        if (isNaN(baseDate.getTime())) return;
        
        this.forecastSelect.innerHTML = '';
        
        for (let i = 0; i < 24; i++) {
            const forecastDate = new Date(baseDate);
            const hoursToAdd = i * 3;
            forecastDate.setUTCHours(forecastDate.getUTCHours() + hoursToAdd);
            
            const weekday = this.weekdays[forecastDate.getUTCDay()];
            const month = this.months[forecastDate.getUTCMonth()];
            const day = forecastDate.getUTCDate();
            const year = forecastDate.getUTCFullYear();
            const hours = forecastDate.getUTCHours().toString().padStart(2, '0');
            
            const option = document.createElement('option');
            option.value = i + 1;
            option.textContent = `${weekday}, ${day} ${month} ${year} ${hours} UTC (+${hoursToAdd} Hrs)`;
            
            if (i === 0) option.selected = true;
            
            this.forecastSelect.appendChild(option);
        }
    }

    checkUrlParams() {
        if (window.location.search) {
            this.loadFromUrlParams();
        }
    }

    loadFromUrlParams() {
        const params = new URLSearchParams(window.location.search);
        const datetimeInit = params.get('datetime_init') || '';

        if (datetimeInit && datetimeInit.length === 10) {
            const datePart = datetimeInit.substring(0, 8);
            const formattedDate = `${datePart.substring(0, 4)}-${datePart.substring(4, 6)}-${datePart.substring(6, 8)}`;

            if (this.datePicker) this.datePicker.value = formattedDate;
            if (this.hourSelect) this.hourSelect.value = datetimeInit.substring(8, 10);
        }

        this.updateForecastOptions();

        // Cargar t_index desde URL
        const tIndex = params.get('t_index');
        if (tIndex && this.forecastSelect) {
            this.forecastSelect.value = tIndex;
        }

        this.updateDatetimeInit();
    }

    async handleSubmit(e) {
        e.preventDefault();

        const datetimeInit = this.datetimeInitEl.value;
        if (!/^\d{10}$/.test(datetimeInit)) {
            this.showError('Formato de fecha/hora inválido');
            return;
        }

        this.setLoadingState(true);
        this.clearPlot();

        try {
            const formData = new FormData(this.form);
            
            const response = await fetch('', {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': this.getCSRFToken(),
                },
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.message || `Error ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            if (data.status === 'success') {
                this.displayPlot(data.plot_image);
                this.updateInfo(data);
                this.updateURL();
            } else {
                throw new Error(data.message || 'Error al procesar la solicitud');
            }

        } catch (error) {
            console.error('Error:', error);
            this.showError(`Error: ${error.message || 'Problema al procesar la solicitud'}`);
        } finally {
            this.setLoadingState(false);
        }
    }

    getCSRFToken() {
        const cookieValue = document.cookie.match('(^|;)\\s*csrftoken\\s*=\\s*([^;]+)');
        return cookieValue ? cookieValue.pop() : '';
    }

    displayPlot(imageData) {
        this.plotEl.src = 'data:image/png;base64,' + imageData;
        this.plotEl.classList.remove('d-none');
        this.emptyPlotEl.classList.add('d-none');
    }

    clearPlot() {
        this.plotEl.classList.add('d-none');
        this.emptyPlotEl.classList.remove('d-none');
    }

    updateInfo(data) {
        if (data.datetime && this.datetimeInfoEl) {
            this.datetimeInfoEl.innerHTML = `<strong>Fecha/Hora:</strong> ${data.datetime}`;
        }

        if (data.params && this.paramsInfoEl) {
            const selectedOption = this.townSelect.options[this.townSelect.selectedIndex];
            const townName = selectedOption.textContent;
            
            this.paramsInfoEl.innerHTML = `
                <strong>Municipio:</strong> ${townName}<br>
                <strong>Posición:</strong> Lat ${data.params.lat}°, Long ${data.params.long}°
            `;
        }
    }

    updateURL() {
        const selectedOption = this.townSelect.options[this.townSelect.selectedIndex];
        const lat = selectedOption.getAttribute('data-lat');
        const long = selectedOption.getAttribute('data-long');
        
        const params = {
            datetime_init: this.datetimeInitEl.value,
            lat: lat,
            long: long,
            t_index: this.forecastSelect.value
        };
        
        const urlParams = new URLSearchParams(params);
        const newUrl = `${window.location.pathname}?${urlParams}`;
        window.history.pushState({}, '', newUrl);
    }

    setLoadingState(isLoading) {
        if (this.submitBtn) {
            this.submitBtn.disabled = isLoading;
            this.submitBtn.innerHTML = isLoading
                ? '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Procesando...'
                : 'Generar';
        }

        if (this.loadingEl) {
            this.loadingEl.classList.toggle('d-none', !isLoading);
        }
    }

    showError(message) {
        // Crear elemento de alerta si no existe
        let alertEl = document.getElementById('form-alert');
        if (!alertEl) {
            alertEl = document.createElement('div');
            alertEl.id = 'form-alert';
            alertEl.className = 'alert alert-danger alert-dismissible fade show';
            alertEl.innerHTML = `
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            `;
            this.form.prepend(alertEl);
        } else {
            alertEl.innerHTML = `
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            `;
            alertEl.classList.remove('d-none');
        }

        // Auto-ocultar después de 5 segundos
        setTimeout(() => {
            alertEl.classList.add('d-none');
        }, 5000);
    }
}

// Inicializar cuando el DOM esté completamente cargado
document.addEventListener('DOMContentLoaded', () => {
    new SoundingFormHandler();
});