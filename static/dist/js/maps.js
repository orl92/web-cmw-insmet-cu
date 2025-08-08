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
        
        // Verificar que plotContainer existe antes de agregar
        if (this.plotContainer) {
            this.plotContainer.appendChild(container);
        } else {
            console.error('plotContainer no encontrado');
        }
        
        return container;
    }

    showLoading(message, progress = null) {
        this.loadingElement.innerHTML = `
            <div class="text-center py-3">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Cargando...</span>
                </div>
                <p class="mt-2">${message}</p>
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
        if (!this.animationContainer) {
            console.error('animationContainer no disponible');
            return;
        }
        
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
        
        if (this.animationContainer) {
            this.animationContainer.innerHTML = '';
        }
    }

    async withRetries(operation) {
        try {
            return await operation();
        } catch (error) {
            this.retryCount++;

            if (this.retryCount < this.maxRetries) {
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

            // const data = await this.withRetries(() => this.fetchData());
            // console.log('Datos recibidos:', data);

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
    const today = new Date();

    const formatDate = (date) => {
        return date.toISOString().split('T')[0];
    };

    const datepickerElement = document.getElementById('datepicker');
    if (datepickerElement) {
        const datepicker = new Litepicker({
            element: datepickerElement,
            format: 'YYYY-MM-DD',
            lang: 'es-ES',
            resetButton: false,
            buttonText: {
                previousMonth: `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon icon-1"><path d="M15 6l-6 6l6 6" /></svg>`,
                nextMonth: `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon icon-1"><path d="M9 6l6 6l-6 6" /></svg>`
            }
        });

        if (!datepickerElement.value) {
            datepicker.setDate(today);
        }
    }
}

// Código de inicialización cuando el DOM está listo
document.addEventListener('DOMContentLoaded', function() {
    // Inicializar Litepicker primero
    initLitepicker();

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

            if (plotArea) plotArea.style.display = 'block';
            if (loadingIndicator) loadingIndicator.style.display = 'block';

            try {
                // Construir datetime_init a partir de los campos de fecha y hora
                const dateValue = document.getElementById('datepicker').value;
                const hourValue = document.getElementById('hour-select').value;
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

                if (plotTitle) plotTitle.textContent = `${data.var_label} - ${data.datetime_init}`;

                const plotter = new MeteoPlotter({
                    datetimeInit: data.datetime_init,
                    varName: data.var_name,
                    varLabel: data.var_label
                });

                plotter.init();

            } catch (error) {
                console.error('Error:', error);
                if (loadingIndicator) {
                    loadingIndicator.innerHTML = `
                        <div class="alert alert-danger">
                            <strong>Error:</strong> ${error.message}
                        </div>
                    `;
                }
            }
        });
    }
});

// Para depuración
window.MeteoPlotter = MeteoPlotter;