class MeteogramFormHandler {
    constructor() {
        this.meteogramInstance = null;
        this.apiBaseUrl = 'https://modelo.cmw.insmet.cu';
        this.initElements();
        this.bindEvents();
        this.loadInitialData();
        this.initLitepicker();
        this.setupDatetimeHandlers();
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
        document.getElementById('datepicker')?.addEventListener('change', () => this.updateDatetimeInit());
        document.getElementById('hour-select')?.addEventListener('change', () => this.updateDatetimeInit());
    }

    updateDatetimeInit() {
        const dateValue = document.getElementById('datepicker').value;
        const hourValue = document.getElementById('hour-select').value;
        const formattedDate = dateValue.replace(/-/g, '') + hourValue;
        document.getElementById('datetime-init').value = formattedDate;
    }

    initElements() {
        this.form = document.getElementById('meteogram-form');
        this.submitBtn = document.getElementById('submit-btn');
        this.feedbackEl = document.getElementById('form-feedback');
        this.loadingEl = document.getElementById('loading');
        this.chartContainer = document.getElementById('container');
    }

    bindEvents() {
        this.form.addEventListener('submit', (e) => this.handleSubmit(e));
    }

    loadInitialData() {
        const params = new URLSearchParams(window.location.search);
        let datetimeInit = params.get('datetime_init') || '';

        if (datetimeInit && datetimeInit.length === 10) {
            const datePart = datetimeInit.substring(0, 8);
            const formattedDate = `${datePart.substring(0, 4)}-${datePart.substring(4, 6)}-${datePart.substring(6, 8)}`;
            document.getElementById('datepicker').value = formattedDate;
            document.getElementById('hour-select').value = datetimeInit.substring(8, 10);
        } else {
            const today = new Date().toISOString().split('T')[0];
            document.getElementById('datepicker').value = today;
            document.getElementById('hour-select').value = '00';
        }

        // Cargar el municipio desde los parámetros de la URL si existe
        const townId = params.get('town');
        if (townId) {
            document.getElementById('id_town').value = townId;
        }

        this.updateDatetimeInit();
    }

    async handleSubmit(e) {
        e.preventDefault();

        const datetimeInit = document.getElementById('datetime-init').value;
        if (!/^\d{10}$/.test(datetimeInit)) {
            this.showFeedback('Formato de fecha/hora inválido', 'danger');
            return;
        }

        this.setLoadingState(true);
        this.clearFeedback();
        this.clearChart();

        try {
            const formData = new FormData(this.form);
            const params = {
                datetime_init: formData.get('datetime_init'),
                town: formData.get('town')  // Solo enviamos datetime_init y town
            };

            if (!params.datetime_init || !params.town) {
                throw new Error('Todos los campos son requeridos');
            }

            // Enviar el formulario a la vista de Django
            const response = await fetch('', {
                method: 'POST',
                body: new URLSearchParams(params),
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': this.getCSRFToken(),
                }
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.message || `Error ${response.status}: ${response.statusText}`);
            }

            const responseData = await response.json();

            if (responseData.status !== 'success' || !responseData.data) {
                throw new Error(responseData.message || 'Respuesta inesperada del servidor');
            }

            // Obtener las coordenadas del municipio seleccionado para el gráfico
            const selectedOption = document.getElementById('id_town').selectedOptions[0];
            const lat = parseFloat(selectedOption.getAttribute('data-lat'));
            const long = parseFloat(selectedOption.getAttribute('data-long'));

            this.updateMeteogram(responseData, lat, long);
            this.showFeedback('Datos meteorológicos actualizados correctamente ✅', 'success');
            this.updateURL(params, lat, long);

        } catch (error) {
            console.error('Error:', error);
            this.showFeedback(`Error: ${error.message || 'Problema al procesar la solicitud'} ❌`, 'danger');
        } finally {
            this.setLoadingState(false);
        }
    }

    getCSRFToken() {
        const cookieValue = document.cookie.match('(^|;)\\s*csrftoken\\s*=\\s*([^;]+)');
        return cookieValue ? cookieValue.pop() : '';
    }

    updateMeteogram(formattedResponse, lat, long) {
        if (!formattedResponse || !formattedResponse.data || !formattedResponse.data.times) {
            throw new Error('Datos meteorológicos no válidos o vacíos');
        }

        const options = {
            lat: lat,
            long: long,
            timezone: 'UTC',
            apiBaseUrl: this.apiBaseUrl
        };

        if (this.meteogramInstance) {
            try {
                this.meteogramInstance.destroy();
            } catch (e) {
                console.warn('Error al limpiar instancia anterior:', e);
            }
        }

        try {
            this.meteogramInstance = new Meteogram(formattedResponse.data, 'container', options);
        } catch (error) {
            console.error('Error al crear meteograma:', error);
            throw new Error(`Error al crear gráfico: ${error.message}`);
        }
    }

    updateURL(params, lat, long) {
        // Incluir las coordenadas en la URL para compartir
        const urlParams = new URLSearchParams({
            datetime_init: params.datetime_init,
            town: params.town,
            lat: lat,
            long: long
        });
        const newUrl = `${window.location.pathname}?${urlParams}`;
        window.history.pushState({}, '', newUrl);
    }

    clearChart() {
        if (this.chartContainer) {
            this.chartContainer.innerHTML = '<div id="loading" style="display: none;">⏳ Cargando datos meteorológicos...</div>';
        }
    }

    showFeedback(message, type = 'success') {
        if (this.feedbackEl) {
            this.feedbackEl.innerHTML = `
                <div class="alert alert-${type}">
                    ${message}
                </div>
            `;
        }
    }

    clearFeedback() {
        if (this.feedbackEl) {
            this.feedbackEl.innerHTML = '';
        }
    }

    setLoadingState(isLoading) {
        if (this.submitBtn) {
            this.submitBtn.disabled = isLoading;
            this.submitBtn.innerHTML = isLoading
                ? '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Procesando...'
                : 'Generar';
        }

        if (this.loadingEl) {
            this.loadingEl.style.display = isLoading ? 'block' : 'none';
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new MeteogramFormHandler();
});