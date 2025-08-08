class SoundingPlotter {
    constructor() {
        this.form = $('#sounding-form');
        this.plot = $('#sounding-plot');
        this.loading = $('#loading');
        this.emptyPlotMessage = $('#empty-plot');
        this.datetimeInfo = $('#datetime-info');
        this.paramsInfo = $('#params-info');
        this.plotTitle = $('#plot-title');

        // Referencias a elementos
        this.datePicker = document.getElementById('datepicker');
        this.hourSelect = document.getElementById('hour-select');
        this.forecastSelect = document.getElementById('forecast-select'); // Este es el t_index

        this.initEvents();
        this.setDefaultDatetime();
        this.initLitepicker();
        this.setupDatetimeHandlers();
        
        // Inicializar el select de previsión
        this.initForecastSelect();
        this.checkUrlParams();
    }

    setDefaultDatetime() {
        // Establecer fecha actual si no hay valor
        if (!this.datePicker.value) {
            const today = new Date().toISOString().split('T')[0];
            this.datePicker.value = today;
        }
        
        // Establecer hora 00 por defecto si no hay selección
        if (!this.hourSelect.value) {
            this.hourSelect.value = '00';
        }
        
        // Actualizar campo oculto
        this.updateDatetimeInit();
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

    updateDatetimeInit() {
        const dateValue = this.datePicker.value;
        const hourValue = this.hourSelect.value;

        if (dateValue && hourValue) {
            const formattedDate = dateValue.replace(/-/g, '') + hourValue;
            this.form.find('[name="datetime_init"]').val(formattedDate);
        }
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
            option.value = i + 1; // Este valor será el t_index
            option.textContent = `${weekday}, ${day} ${month} ${year} ${hours} UTC (+${hoursToAdd} Hrs)`;
            
            if (i === 0) option.selected = true;
            
            this.forecastSelect.appendChild(option);
        }
    }

    initEvents() {
        this.form.on('submit', (e) => this.handleSubmit(e));
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

        this.form.find('[name="lat"]').val(params.get('lat') || '');
        this.form.find('[name="long"]').val(params.get('long') || '');
        
        // Cargar t_index desde URL
        const tIndex = params.get('t_index');
        if (tIndex && this.forecastSelect) {
            this.forecastSelect.value = tIndex;
        }

        this.updateDatetimeInit();
    }

    handleSubmit(e) {
        e.preventDefault();
        this.logFormData();
        this.submitForm();
    }
    
    logFormData() {
        const formData = {
            datetime_init: this.form.find('[name="datetime_init"]').val(),
            lat: this.form.find('[name="lat"]').val(),
            long: this.form.find('[name="long"]').val(),
            t_index: this.forecastSelect.value // Este es el valor importante
        };
        console.log("Datos del formulario a enviar:", formData);
    }

    submitForm() {
        const datetimeInit = this.form.find('[name="datetime_init"]').val();
        if (!/^\d{10}$/.test(datetimeInit)) {
            this.showError('Formato de fecha/hora inválido');
            return;
        }

        this.showLoading();

        $.ajax({
            type: 'POST',
            url: this.form.attr('action'),
            data: this.form.serialize(),
            success: (response) => this.handleSuccess(response),
            error: (xhr) => this.handleError(xhr),
            complete: () => this.hideLoading()
        });
    }

    handleSuccess(response) {
        if (response.status === 'success') {
            this.displayPlot(response.plot_image);
            this.updateInfo(response);
            this.updateUrl();
        } else {
            this.showError(response.message || 'Error desconocido');
            this.emptyPlotMessage.removeClass('d-none');
        }
    }

    handleError(xhr) {
        try {
            const error = JSON.parse(xhr.responseText);
            this.showError(error.message || 'Error en el servidor');
        } catch (e) {
            this.showError('Error al procesar la solicitud');
        }
        this.emptyPlotMessage.removeClass('d-none');
    }

    displayPlot(imageData) {
        this.plot.attr('src', 'data:image/png;base64,' + imageData).removeClass('d-none');
        this.emptyPlotMessage.addClass('d-none');
    }

    updateInfo(response) {
        if (response.datetime) {
            this.datetimeInfo.html(`<strong>Fecha/Hora:</strong> ${response.datetime}`);
        }

        if (response.params) {
            // Obtener el nombre del municipio seleccionado
            const townSelect = document.getElementById('id_town');
            const selectedTown = townSelect.options[townSelect.selectedIndex].text;
            
            this.paramsInfo.html(`
                <strong>Municipio:</strong> ${selectedTown}<br>
                <strong>Posición:</strong> Lat ${response.params.lat}°, Long ${response.params.long}°
            `);
        }
    }

    updateUrl() {
        const params = {
            datetime_init: this.form.find('[name="datetime_init"]').val(),
            lat: this.form.find('[name="lat"]').val(),
            long: this.form.find('[name="long"]').val(),
            t_index: this.forecastSelect.value // Este es el valor importante
        };

        const queryString = new URLSearchParams(params).toString();
        window.history.pushState({}, '', `?${queryString}`);
    }

    showLoading() {
        this.loading.show();
        this.plot.addClass('d-none');
        this.emptyPlotMessage.addClass('d-none');
        this.form.find('button[type="submit"]').prop('disabled', true)
            .html('<span class="spinner-border spinner-border-sm" role="status"></span> Procesando...');
    }

    hideLoading() {
        this.loading.hide();
        this.form.find('button[type="submit"]').prop('disabled', false)
            .html('Generar');
    }

    showError(message) {
        const errorAlert = $(`
            <div class="alert alert-danger alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `);

        this.form.prepend(errorAlert);

        setTimeout(() => {
            errorAlert.alert('close');
        }, 5000);
    }
}

$(document).ready(function () {
    new SoundingPlotter();
});