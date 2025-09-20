// static/dist/js/sounding-form.js
class SoundingFormHandler {
    constructor() {
        // Primero inicializar las variables de días y meses
        this.weekdays = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'];
        this.months = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
                       'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'];
        
        this.initElements();
        this.setCurrentDateAndTime();
        this.bindEvents();
        this.initLitepicker();
        this.setupDatetimeHandlers();
        this.setupTownChangeHandler();
        this.updateForecastOptions(); // Actualizar opciones de previsión
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

    // Nuevo método para establecer fecha y hora actual
    setCurrentDateAndTime() {
        const now = new Date();
        const year = now.getUTCFullYear();
        const month = (now.getUTCMonth() + 1).toString().padStart(2, '0');
        const day = now.getUTCDate().toString().padStart(2, '0');
        const currentDate = `${year}-${month}-${day}`;
        
        // Establecer fecha actual en el input solo si no hay valor previo
        if (this.datePicker && !this.datePicker.value) {
            this.datePicker.value = currentDate;
        }
        
        // Establecer hora 00 UTC por defecto si no hay valor
        if (this.hourSelect && !this.hourSelect.value) {
            this.hourSelect.value = '00';
        }
        
        // Actualizar campo oculto de datetime
        this.updateDatetimeInit();
    }

    bindEvents() {
        this.form.addEventListener('submit', (e) => this.handleSubmit(e));
    }

    initLitepicker() {
        const datepickerElement = document.getElementById('datepicker');
        if (datepickerElement) {
            new Litepicker({
                element: datepickerElement,
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
        if (dateValue && hourValue) {
            const formattedDate = dateValue.replace(/-/g, '') + hourValue;
            this.datetimeInitEl.value = formattedDate;
        }
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
            
            // Validar que la fecha sea válida
            if (isNaN(forecastDate.getTime())) {
                console.error('Fecha inválida en previsión');
                continue;
            }
            
            const dayOfWeek = forecastDate.getUTCDay();
            const monthIndex = forecastDate.getUTCMonth();
            
            // Validar índices
            if (dayOfWeek < 0 || dayOfWeek >= this.weekdays.length) {
                console.error('Índice de día fuera de rango:', dayOfWeek);
                continue;
            }
            
            if (monthIndex < 0 || monthIndex >= this.months.length) {
                console.error('Índice de mes fuera de rango:', monthIndex);
                continue;
            }
            
            const weekday = this.weekdays[dayOfWeek];
            const month = this.months[monthIndex];
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
        } else {
            // Si no hay parámetros en la URL, actualizar con valores por defecto
            this.updateDatetimeInit();
            this.updateForecastOptions();
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

        // Cargar t_index desde URL
        const tIndex = params.get('t_index');
        if (tIndex && this.forecastSelect) {
            this.forecastSelect.value = tIndex;
        }

        this.updateDatetimeInit();
        this.updateForecastOptions();
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