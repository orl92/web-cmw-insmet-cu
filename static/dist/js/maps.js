// Clase principal para manejar la visualización meteorológica
class MeteoPlotter {
    constructor(params) {
        // Configuración inicial
        this.datetimeInit = params.datetimeInit;
        this.varName = params.varName;
        this.varLabel = params.varLabel;

        // Elementos del DOM
        this.plotContainer = document.getElementById('plot-container');
        this.loadingElement = document.getElementById('loading');
        this.animationContainer = document.getElementById('animation-container') || this.createAnimationContainer();
        
        // Eliminada la referencia a statusElement
        // this.statusElement = document.getElementById('status-message') || this.createStatusElement();

        // Configuración de reintentos
        this.maxRetries = 3;
        this.retryDelay = 2000;
        this.retryCount = 0;

        // Estado de la animación
        this.animationHTML = null;
        this.animationScripts = [];
    }

    createAnimationContainer() {
        const container = document.createElement('div');
        container.id = 'animation-container';
        container.className = 'animation-container';
        this.plotContainer.appendChild(container);
        return container;
    }

    // Eliminado el método createStatusElement()
    // createStatusElement() {
    //     const elem = document.createElement('div');
    //     elem.id = 'status-message';
    //     elem.className = 'status-message';
    //     this.plotContainer.appendChild(elem);
    //     return elem;
    // }

    // Eliminado el método showStatus()
    // showStatus(message, type = 'info') {
    //     const icons = {
    //         error: 'exclamation-triangle',
    //         warning: 'exclamation-circle',
    //         success: 'check-circle',
    //         info: 'info-circle'
    //     };
    //
    //     this.statusElement.innerHTML = `
    //         <div class="alert alert-${type}">
    //             <i class="fas fa-${icons[type] || 'info-circle'} me-2"></i>
    //             ${message}
    //         </div>
    //     `;
    // }

    showLoading(message, progress = null) {
        let progressBar = '';
        if (progress !== null) {
            progressBar = `
                <div class="progress mt-2" style="height: 6px;">
                    <div class="progress-bar progress-bar-striped progress-bar-animated" 
                         style="width: ${progress}%"></div>
                </div>
            `;
        }

        this.loadingElement.innerHTML = `
            <div class="text-center py-3">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Cargando...</span>
                </div>
                <p class="mt-2">${message}</p>
                ${progressBar}
                ${this.retryCount > 0 ? 
                 `<p class="text-muted small mt-2">Intento ${this.retryCount + 1} de ${this.maxRetries}</p>` : ''}
            </div>
        `;
    }

    showRecoveryOptions(errorMessage) {
        this.loadingElement.innerHTML = `
            <div class="alert alert-danger">
                <strong>Error:</strong> ${errorMessage}
                <div class="mt-3 d-flex justify-content-center">
                    <button class="btn btn-sm btn-primary me-2" id="retry-button">Reintentar</button>
                    <button class="btn btn-sm btn-secondary" id="back-button">Volver</button>
                </div>
            </div>
        `;

        document.getElementById('retry-button').addEventListener('click', () => {
            this.retryCount = 0;
            this.init();
        });

        document.getElementById('back-button').addEventListener('click', () => {
            this.cleanupAnimation();
            document.getElementById('plot-area').style.display = 'none';
        });
    }

    async fetchData() {
        try {
            this.showLoading('Obteniendo datos meteorológicos...', 25);

            const response = await fetch(
                `/api/fetch-data/?datetime_init=${encodeURIComponent(this.datetimeInit)}&var_name=${encodeURIComponent(this.varName)}`,
                {
                    headers: { 'X-Requested-With': 'XMLHttpRequest' }
                }
            );

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || `Error HTTP: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error en fetchData:', error);
            throw error;
        }
    }

    async generatePlot() {
        try {
            this.showLoading('Generando animación interactiva...', 50);

            const response = await fetch(
                `/api/generate-plot/?var_name=${encodeURIComponent(this.varName)}`,
                {
                    headers: { 'X-Requested-With': 'XMLHttpRequest' }
                }
            );

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || `Error HTTP: ${response.status}`);
            }

            const data = await response.json();
            this.animationHTML = data.animation_html;
            return data;
        } catch (error) {
            console.error('Error en generatePlot:', error);
            throw error;
        }
    }

    showAnimation() {
        this.animationContainer.innerHTML = '';
        this.loadingElement.style.display = 'none';

        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = this.animationHTML;

        this.animationScripts = Array.from(tempDiv.querySelectorAll('script'));

        this.animationContainer.innerHTML = tempDiv.innerHTML;

        this.animationScripts.forEach(script => {
            const newScript = document.createElement('script');
            if (script.src) {
                newScript.src = script.src;
            } else {
                newScript.textContent = script.textContent;
            }
            document.body.appendChild(newScript);
        });

        const animationDiv = this.animationContainer.querySelector('div');
        if (animationDiv) {
            animationDiv.style.maxWidth = '100%';
            animationDiv.style.overflow = 'hidden';
        }
    }

    cleanupAnimation() {
        this.animationScripts.forEach(script => {
            if (script.parentNode) {
                script.parentNode.removeChild(script);
            }
        });
        this.animationScripts = [];
        this.animationContainer.innerHTML = '';
    }

    async withRetries(operation) {
        try {
            return await operation();
        } catch (error) {
            this.retryCount++;

            if (this.retryCount < this.maxRetries) {
                // Eliminada la llamada a showStatus()
                // this.showStatus(`Reintentando operación... (${this.retryCount}/${this.maxRetries})`, 'warning');
                await new Promise(resolve => setTimeout(resolve, this.retryDelay));
                return this.withRetries(operation);
            } else {
                throw error;
            }
        }
    }

    async init() {
        try {
            this.cleanupAnimation();

            const data = await this.withRetries(() => this.fetchData());
            console.log('Datos recibidos:', data);

            const plotData = await this.withRetries(() => this.generatePlot());
            console.log('Animación generada:', plotData);

            this.showAnimation();

        } catch (error) {
            console.error('Error en MeteoPlotter:', error);
            this.showRecoveryOptions(error.message);

            console.group('Detalles del error');
            console.error('Variable:', this.varName);
            console.error('Fecha:', this.datetimeInit);
            console.error('Mensaje:', error.message);
            console.error('Stack:', error.stack);
            console.groupEnd();
        } finally {
            this.retryCount = 0;
        }
    }
}

// Función para inicializar el Litepicker
function initLitepicker() {
    // Calcular fechas límite (3 días atrás y 1 día adelante)
    const today = new Date();
    // const threeDaysAgo = new Date();
    // threeDaysAgo.setDate(today.getDate() - 3);
    // const oneDayLater = new Date();
    // oneDayLater.setDate(today.getDate() + 1);

    // Formatear fechas para Litepicker (YYYY-MM-DD)
    const formatDate = (date) => {
        return date.toISOString().split('T')[0];
    };

    // Configurar Litepicker
    const datepickerElement = document.getElementById('datepicker');
    if (datepickerElement) {
        const datepicker = new Litepicker({
            element: datepickerElement,
            format: 'YYYY-MM-DD',
            lang: 'es-ES',
            // minDate: formatDate(threeDaysAgo),
            // maxDate: formatDate(oneDayLater),
            resetButton: false,
            buttonText: {
                previousMonth: `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon icon-1"><path d="M15 6l-6 6l6 6" /></svg>`,
                nextMonth: `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon icon-1"><path d="M9 6l6 6l-6 6" /></svg>`
            }
        });

        // Establecer fecha actual por defecto si no hay valor inicial
        if (!datepickerElement.value) {
            datepicker.setDate(today);
        }
    }
}

// Código de inicialización cuando el DOM está listo
document.addEventListener('DOMContentLoaded', function() {
    // Inicializar Litepicker primero
    initLitepicker();

    // Función para actualizar el campo datetime_init
    function updateDatetimeInit() {
        // Esta función ya no es necesaria si no tenemos un campo oculto
    }

    // Actualizar cuando cambia la fecha o la hora
    document.getElementById('datepicker')?.addEventListener('change', updateDatetimeInit);
    document.getElementById('hour-select')?.addEventListener('change', updateDatetimeInit);

    const form = document.getElementById('data-form');
    const plotArea = document.getElementById('plot-area');
    const plotTitle = document.getElementById('plot-title');
    const loadingIndicator = document.getElementById('loading');

    if (form) {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();

            if (!form.checkValidity()) {
                e.stopPropagation();
                form.classList.add('was-validated');
                return;
            }

            plotArea.style.display = 'block';
            loadingIndicator.style.display = 'block';

            try {
                // Construir datetime_init a partir de los campos de fecha y hora
                const dateValue = document.getElementById('datepicker').value;
                const hourValue = document.getElementById('hour-select').value;
                // Formatear la fecha: YYYYMMDD
                const formattedDate = dateValue.replace(/-/g, '');
                const datetimeInit = formattedDate + hourValue;

                const formData = {
                    datetime_init: datetimeInit,
                    var_name: form.var_name.value,
                    csrfmiddlewaretoken: document.querySelector('[name=csrfmiddlewaretoken]').value
                };

                const response = await fetch('', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': formData.csrfmiddlewaretoken
                    },
                    body: JSON.stringify(formData)
                });

                if (!response.ok) {
                    const error = await response.text();
                    throw new Error(error || 'Error en el servidor');
                }

                const data = await response.json();

                if (data.status !== 'success') {
                    throw new Error(JSON.stringify(data.errors));
                }

                plotTitle.textContent = `${data.var_label} - ${data.datetime_init}`;

                const plotter = new MeteoPlotter({
                    datetimeInit: data.datetime_init,
                    varName: data.var_name,
                    varLabel: data.var_label
                });

                plotter.init();

            } catch (error) {
                console.error('Error:', error);
                loadingIndicator.innerHTML = `
                    <div class="alert alert-danger">
                        <strong>Error:</strong> ${error.message}
                    </div>
                `;
            }
        });
    }
});

// Para depuración
window.MeteoPlotter = MeteoPlotter;