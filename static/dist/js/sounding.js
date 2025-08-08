class SoundingPlotter {
    constructor() {
        this.form = $('#sounding-form');
        this.plot = $('#sounding-plot');
        this.loading = $('#loading');
        this.emptyPlotMessage = $('#empty-plot');
        this.datetimeInfo = $('#datetime-info');
        this.paramsInfo = $('#params-info');
        this.plotTitle = $('#plot-title');

        this.initEvents();
        this.checkUrlParams();

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
        const dateValue = document.getElementById('datepicker').value; // Formato YYYY-MM-DD
        const hourValue = document.getElementById('hour-select').value; // HH

        // Convertir a YYYYMMDDHH
        const formattedDate = dateValue.replace(/-/g, '') + hourValue;
        this.form.find('[name="datetime_init"]').val(formattedDate);
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

            document.getElementById('datepicker').value = formattedDate;
            document.getElementById('hour-select').value = datetimeInit.substring(8, 10);
            // Ocultar mensaje inicial cuando hay parámetros
            this.emptyPlotMessage.addClass('d-none')
        } else {
            const today = new Date().toISOString().split('T')[0];
            document.getElementById('datepicker').value = today;
            document.getElementById('hour-select').value = '12';
        }

        this.form.find('[name="lat"]').val(params.get('lat') || '');
        this.form.find('[name="long"]').val(params.get('long') || '');
        this.form.find('[name="t_index"]').val(params.get('t_index') || '0');
        this.updateDatetimeInit();
        this.submitForm();
    }

    handleSubmit(e) {
        e.preventDefault();
        this.submitForm();
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
            // Mostrar mensaje inicial en caso de error
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
        // Mostrar mensaje inicial en caso de error
        this.emptyPlotMessage.removeClass('d-none');
    }

    displayPlot(imageData) {
        this.plot.attr('src', 'data:image/png;base64,' + imageData).removeClass('d-none');
        // Asegurar que el mensaje inicial esté oculto
        this.emptyPlotMessage.addClass('d-none');
    }

    updateInfo(response) {
        if (response.datetime) {
            this.datetimeInfo.html(`<strong>Fecha/Hora:</strong> ${response.datetime}`);
        }

        if (response.params) {
            const tIndexLabels = {
                '0': 'Ninguno',
                '1': 'Showalter',
                '2': 'Lifted',
                '3': 'CAPE'
            };

            this.paramsInfo.html(`
                <strong>Posición:</strong> Lat ${response.params.lat}°, Long ${response.params.long}° | 
                <strong>Índice T:</strong> ${tIndexLabels[response.params.t_index] || 'Desconocido'}
            `);
        }
    }

    updateUrl() {
        const params = {
            datetime_init: this.form.find('[name="datetime_init"]').val(),
            lat: this.form.find('[name="lat"]').val(),
            long: this.form.find('[name="long"]').val(),
            t_index: this.form.find('[name="t_index"]').val()
        };

        const queryString = new URLSearchParams(params).toString();
        window.history.pushState({}, '', `?${queryString}`);
    }

    showLoading() {
        this.loading.show();
        this.plot.addClass('d-none');
        // Ocultar mensaje inicial al comenzar carga
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

// Inicialización cuando el DOM está listo
$(document).ready(function () {
    new SoundingPlotter();
});