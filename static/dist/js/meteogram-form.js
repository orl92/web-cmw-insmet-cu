class MeteogramFormHandler {
    constructor() {
        this.meteogramInstance = null;
        this.apiBaseUrl = 'https://modelo.cmw.insmet.cu'; // API en puerto 8000, http://127.0.0.1:8000
        this.initElements();
        this.bindEvents();
        this.loadInitialData();
        initLitepicker();
        this.setupDatetimeHandlers();
    }

    setupDatetimeHandlers() {
        // Actualizar datetime_init cuando cambian fecha u hora
        document.getElementById('datepicker')?.addEventListener('change', () => this.updateDatetimeInit());
        document.getElementById('hour-select')?.addEventListener('change', () => this.updateDatetimeInit());
    }

    // updateDatetimeInit() {
    //     const dateValue = document.getElementById('datepicker').value;
    //     const hourValue = document.getElementById('hour-select').value;
    //     const formattedDate = dateValue.replace(/-/g, '');
    //     document.getElementById('datetime-init').value = formattedDate + hourValue;
    // }

    updateDatetimeInit() {
        const dateValue = document.getElementById('datepicker').value; // Formato YYYY-MM-DD
        const hourValue = document.getElementById('hour-select').value; // HH

        // Convertir a YYYYMMDDHH
        const formattedDate = dateValue.replace(/-/g, '') + hourValue;
        document.getElementById('datetime-init').value = formattedDate;

        console.log('datetime_init enviado:', formattedDate); // Para depuración
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

    // loadInitialData() {
    //     const params = new URLSearchParams(window.location.search);
    //     const initialData = {
    //         datetime_init: params.get('datetime_init') || '2025071806',
    //         lat: parseFloat(params.get('lat')) || 20.715,
    //         long: parseFloat(params.get('long')) || -77.993
    //     };
    //
    //     this.form.querySelector('[name="datetime_init"]').value = initialData.datetime_init;
    //     this.form.querySelector('[name="lat"]').value = initialData.lat;
    //     this.form.querySelector('[name="long"]').value = initialData.long;
    //
    //     this.handleSubmit(new Event('submit'), true);
    // }

    loadInitialData() {
        const params = new URLSearchParams(window.location.search);
        let datetimeInit = params.get('datetime_init') || '';
        const initialData = {
            lat: parseFloat(params.get('lat')) || 20.715,
            long: parseFloat(params.get('long')) || -77.993
        };

        if (datetimeInit && datetimeInit.length === 10) {
            const datePart = datetimeInit.substring(0, 8);
            const formattedDate = `${datePart.substring(0, 4)}-${datePart.substring(4, 6)}-${datePart.substring(6, 8)}`;

            document.getElementById('datepicker').value = formattedDate;
            document.getElementById('hour-select').value = datetimeInit.substring(8, 10);
        } else {
            const today = new Date().toISOString().split('T')[0];
            document.getElementById('datepicker').value = today;
            document.getElementById('hour-select').value = '12';
        }

        this.form.querySelector('[name="lat"]').value = initialData.lat;
        this.form.querySelector('[name="long"]').value = initialData.long;
        this.updateDatetimeInit();
    }

    async handleSubmit(e, isInitialLoad = false) {
        if (!isInitialLoad) e.preventDefault();

        // Verificar formato de datetime_init
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
                lat: formData.get('lat'),
                long: formData.get('long')
            };

            // Validación básica
            if (!params.datetime_init || !params.lat || !params.long) {
                throw new Error('Todos los campos son requeridos');
            }

            const apiResponse = await this.fetchMeteogramData(params);

            // Verificar estructura de respuesta
            if (!apiResponse || !apiResponse.times || !apiResponse.T2) {
                throw new Error('La API devolvió una estructura de datos inesperada');
            }

            // Formatear respuesta para el meteograma
            const formattedData = {
                status: 'success',
                data: apiResponse
            };

            this.updateMeteogram(formattedData);
            this.showFeedback('Datos meteorológicos actualizados correctamente ✅', 'success');
            this.updateURL(params);

        } catch (error) {
            console.error('Error:', error);
            this.showFeedback(`Error: ${error.message || 'Problema al procesar la solicitud'} ❌`, 'danger');

            if (error.response) {
                console.error('Detalles del error:', await error.response.json());
            }
        } finally {
            this.setLoadingState(false);
        }
    }

    async fetchMeteogramData(params) {
        const url = `${this.apiBaseUrl}/api/meteogram/?datetime_init=${params.datetime_init}&lat=${params.lat}&long=${params.long}`;
        console.log('Solicitando datos a:', url);

        const response = await fetch(url, {
            method: 'GET',
            // mode: 'no-cors',
            headers: {
                'Accept': 'application/json'
            }
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            const error = new Error(errorData.message || `Error ${response.status}: ${response.statusText}`);
            error.response = response;
            throw error;
        }

        return await response.json();
    }

    updateMeteogram(formattedResponse) {
        if (!formattedResponse || !formattedResponse.data || !formattedResponse.data.times) {
            throw new Error('Datos meteorológicos no válidos o vacíos');
        }

        const options = {
            lat: parseFloat(this.form.querySelector('[name="lat"]').value),
            long: parseFloat(this.form.querySelector('[name="long"]').value),
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

    updateURL(params) {
        const newUrl = `${window.location.pathname}?${new URLSearchParams(params)}`;
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
                : '<span class="weather-icon">☀️</span> Generar Meteograma';
        }

        if (this.loadingEl) {
            this.loadingEl.style.display = isLoading ? 'block' : 'none';
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new MeteogramFormHandler();
});