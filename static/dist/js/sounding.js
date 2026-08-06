// static/dist/js/sounding.js
class SoundingFormHandler {
    constructor() {
        this.weekdays = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'];
        this.months = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                       'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'];

        this.initElements();
        this.setCurrentDateAndTime();
        this.bindEvents();
        this.initLitepicker();
        this.setupDatetimeHandlers();
        this.setupTownChangeHandler();
        this.updateForecastOptions();
        this.checkUrlParams();

        this.autoHideTimeout = null;

        // Carga inicial automática después de un breve delay
        // para asegurar que todo está inicializado
        setTimeout(() => {
            this.loadInitialData();
        }, 100);
    }

    initElements() {
        this.form = document.getElementById('sounding-form');
        this.submitBtn = document.getElementById('submit-btn');
        this.plotEl = document.getElementById('sounding-plot');
        this.plotArea = document.getElementById('plot-area');
        this.errorContainer = document.getElementById('error-container');
        this.errorMessageElement = document.getElementById('error-message');
        this.datePicker = document.getElementById('datepicker');
        this.hourSelect = document.getElementById('hour-select');
        this.forecastSelect = document.getElementById('forecast-select');
        this.datetimeInitEl = document.getElementById('datetime-init');
        this.townSelect = document.getElementById('id_town');
    }

    setCurrentDateAndTime() {
        const now = new Date();
        const year = now.getUTCFullYear();
        const month = (now.getUTCMonth() + 1).toString().padStart(2, '0');
        const day = now.getUTCDate().toString().padStart(2, '0');
        const currentDate = `${year}-${month}-${day}`;

        // Solo establecer valores si no existen ya (por ejemplo, de parámetros URL)
        if (this.datePicker && !this.datePicker.value) {
            this.datePicker.value = currentDate;
        }

        if (this.hourSelect && !this.hourSelect.value) {
            this.hourSelect.value = '00';
        }

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
                    previousMonth: '<i class="ti ti-chevron-left" style="font-size:24px;line-height:1"></i>',
                    nextMonth: '<i class="ti ti-chevron-right" style="font-size:24px;line-height:1"></i>'
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

            if (isNaN(forecastDate.getTime())) {
                console.error('Fecha inválida en previsión');
                continue;
            }

            const dayOfWeek = forecastDate.getUTCDay();
            const monthIndex = forecastDate.getUTCMonth();

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
        const params = new URLSearchParams(window.location.search);

        // Verificar si hay parámetros en la URL
        if (params.toString()) {
            const datetimeInit = params.get('datetime_init') || '';

            if (datetimeInit && datetimeInit.length === 10) {
                const datePart = datetimeInit.substring(0, 8);
                const formattedDate = `${datePart.substring(0, 4)}-${datePart.substring(4, 6)}-${datePart.substring(6, 8)}`;

                if (this.datePicker) this.datePicker.value = formattedDate;
                if (this.hourSelect) this.hourSelect.value = datetimeInit.substring(8, 10);
            }

            const tIndex = params.get('t_index');
            if (tIndex && this.forecastSelect) {
                this.forecastSelect.value = tIndex;
            }
        }

        this.updateDatetimeInit();
        this.updateForecastOptions();
    }

    loadInitialData() {
        // Forzar actualización de datetime-init antes de enviar
        this.updateDatetimeInit();

        // Simular envío del formulario para cargar datos iniciales
        setTimeout(() => {
            this.handleSubmit(new Event('submit'));
        }, 100);
    }

    showError(message) {
        if (!this.errorContainer || !this.errorMessageElement) {
            console.error('Error: No se pudo encontrar el contenedor de error');
            return;
        }

        if (this.autoHideTimeout) {
            clearTimeout(this.autoHideTimeout);
            this.autoHideTimeout = null;
        }

        this.errorMessageElement.textContent = message;

        if (this.plotArea) {
            this.plotArea.style.display = 'block';
        }

        this.errorContainer.style.display = 'block';
        this.hidePlot();

        this.autoHideTimeout = setTimeout(() => {
            this.hideError();
        }, 8000);
    }

    hideError() {
        if (this.errorContainer) {
            this.errorContainer.style.display = 'none';
        }

        if (this.autoHideTimeout) {
            clearTimeout(this.autoHideTimeout);
            this.autoHideTimeout = null;
        }
    }

    showPlotArea() {
        if (this.plotArea) {
            this.plotArea.style.display = 'block';
        }
    }

    hidePlotArea() {
        if (this.plotArea) {
            this.plotArea.style.display = 'none';
        }
    }

    showPlot() {
        if (this.plotEl) {
            this.plotEl.style.display = 'block';
        }
    }

    hidePlot() {
        if (this.plotEl) {
            this.plotEl.style.display = 'none';
        }
    }

    clearPlot() {
        this.hidePlot();
    }

    async handleSubmit(e) {
        e.preventDefault();

        const datetimeInit = this.datetimeInitEl.value;
        if (!/^\d{10}$/.test(datetimeInit)) {
            this.showError(`Formato de fecha/hora inválido: ${datetimeInit}`);
            return;
        }

        if (!this.form.checkValidity()) {
            e.stopPropagation();
            this.form.classList.add('was-validated');
            return;
        }

        // Ocultar error previo
        this.hideError();
        this.setSubmitButtonState(true);

        try {
            const formData = new FormData(this.form);

            const response = await fetch('', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': this.getCSRFToken(),
                }
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.message || `Error ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            if (data.status === 'success') {
                this.displayPlot(data.plot_image);
                this.hideError();
                this.updateURL();
            } else {
                throw new Error(data.message || 'Error al procesar la solicitud');
            }

        } catch (error) {
            console.error('Error:', error);
            this.showError(`Error: ${error.message || 'Problema al procesar la solicitud'}`);
        } finally {
            this.setSubmitButtonState(false);
        }
    }

    getCSRFToken() {
        const cookieValue = document.cookie.match('(^|;)\\s*csrftoken\\s*=\\s*([^;]+)');
        return cookieValue ? cookieValue.pop() : '';
    }

    displayPlot(imageData) {
        if (!imageData) {
            this.showError('No se recibieron datos de imagen');
            return;
        }

        // Mostrar el área del gráfico
        this.showPlotArea();
        this.plotEl.src = 'data:image/png;base64,' + imageData;
        this.showPlot();
    }

    setSubmitButtonState(isLoading) {
        if (this.submitBtn) {
            this.submitBtn.disabled = isLoading;
            this.submitBtn.textContent = isLoading ? 'Cargando...' : 'Generar';
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
        const newUrl = `${window.location.pathname}?${urlParams.toString()}`;
        window.history.pushState({}, '', newUrl);
    }
}

// Inicializar cuando el DOM esté completamente cargado
document.addEventListener('DOMContentLoaded', () => {
    new SoundingFormHandler();
});
