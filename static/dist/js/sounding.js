class SoundingPlotter {
    constructor() {
        this.form = $('#sounding-form');
        this.plot = $('#sounding-plot');
        this.loading = $('#loading');
        this.datetimeInfo = $('#datetime-info');
        this.paramsInfo = $('#params-info');
        this.plotTitle = $('#plot-title');

        this.initEvents();
        this.checkUrlParams();
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
        this.form.find('[name="datetime_init"]').val(params.get('datetime_init') || '');
        this.form.find('[name="lat"]').val(params.get('lat') || '');
        this.form.find('[name="long"]').val(params.get('long') || '');
        this.form.find('[name="t_index"]').val(params.get('t_index') || '0');

        this.submitForm();
    }

    handleSubmit(e) {
        e.preventDefault();
        this.submitForm();
    }

    submitForm() {
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
        }
    }

    handleError(xhr) {
        try {
            const error = JSON.parse(xhr.responseText);
            this.showError(error.message || 'Error en el servidor');
        } catch (e) {
            this.showError('Error al procesar la solicitud');
        }
    }

    displayPlot(imageData) {
        this.plot.attr('src', 'data:image/png;base64,' + imageData).removeClass('d-none');
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
        this.form.find('button[type="submit"]').prop('disabled', true)
            .html('<span class="spinner-border spinner-border-sm" role="status"></span> Procesando...');
    }

    hideLoading() {
        this.loading.hide();
        this.form.find('button[type="submit"]').prop('disabled', false)
            .html('<i class="fas fa-chart-line me-2"></i> Generar Sondeo');
    }

    showError(message) {
        const errorAlert = $(`
            <div class="alert alert-danger alert-dismissible fade show" role="alert">
                <i class="fas fa-exclamation-triangle me-2"></i>
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
$(document).ready(function() {
    new SoundingPlotter();
});