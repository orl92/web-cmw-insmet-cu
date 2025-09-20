// Clase principal para manejar la visualización de imágenes meteorológicas
class MeteoPlotter {
    constructor(params) {
        // Configuración inicial
        this.datetimeInit = params.datetimeInit;
        this.varName = params.varName;
        this.varLabel = params.varLabel;
        this.imageUrls = params.imageUrls || [];
        this.simulationDate = params.simulationDate;
        this.count = params.count;

        // Elementos del DOM
        this.plotContainer = document.getElementById('plot-container');
        this.loadingElement = document.getElementById('loading');
        this.galleryContainer = document.getElementById('gallery-container') || this.createGalleryContainer();

        // Estado de la galería
        this.currentImageIndex = 0;
        this.slideshowInterval = null;

        // Configuración de reintentos
        this.maxRetries = 3;
        this.retryDelay = 2000;
        this.retryCount = 0;
    }

    createGalleryContainer() {
        const container = document.createElement('div');
        container.id = 'gallery-container';
        container.className = 'row g-2 g-md-3 mt-3';

        if (this.plotContainer) {
            this.plotContainer.appendChild(container);
        } else {
            console.error('plotContainer no encontrado');
        }

        return container;
    }

    showLoading(message, progress = null) {
        if (!this.loadingElement) return;

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
        if (!this.loadingElement) return;

        this.loadingElement.innerHTML = `
            <div class="alert alert-danger">
                <strong>Error:</strong> ${errorMessage}
                <div class="mt-3 d-flex justify-content-center">
                    <button class="btn btn-sm btn-primary me-2" id="retry-button">Reintentar</button>
                    <button class="btn btn-sm btn-secondary" id="back-button">Volver</button>
                </div>
            </div>
        `;

        // Añadir event listeners después de que el DOM se haya actualizado
        setTimeout(() => {
            const retryButton = document.getElementById('retry-button');
            const backButton = document.getElementById('back-button');

            if (retryButton) {
                retryButton.addEventListener('click', () => {
                    this.retryCount = 0;
                    this.init();
                });
            }

            if (backButton) {
                backButton.addEventListener('click', () => {
                    this.cleanupGallery();
                    const plotArea = document.getElementById('plot-area');
                    if (plotArea) plotArea.style.display = 'none';
                });
            }
        }, 100);
    }

    createImageGallery() {
    if (!this.galleryContainer) return;

    this.galleryContainer.innerHTML = '';

    if (this.imageUrls.length === 0) {
        this.galleryContainer.innerHTML = `
            <div class="col-12 text-center">
                <p class="text-muted">No hay imágenes disponibles para estos parámetros.</p>
            </div>
        `;
        return;
    }

    this.imageUrls.forEach((url, index) => {
        const col = document.createElement('div');
        col.className = 'col-lg-4';

        // Extraer nombre del archivo para el título
        const filename = url.split('/').pop();
        const timePart = filename.split('_').pop().replace('.png', '').replace('T', ' ').replace(/-/g, ':');

        // Usar el proxy para evitar problemas de CORS
        // Extraer la ruta de la imagen desde la URL completa
        const imagePath = url.replace('http://imgwrfserver.cmw.insmet.cu', '');
        const proxyUrl = `/proxy_image_modelo/?image_path=${encodeURIComponent(imagePath)}`;

        col.innerHTML = `
            <div class="row g-2 g-md-3">
                <div class="col-12">
                    <a data-fslightbox="gallery" href="${proxyUrl}" data-caption="${this.varLabel} - ${timePart}">
                        <div class="img-responsive img-responsive-3x1 rounded-3 border" 
                             style="background-image: url(${proxyUrl})">
                        </div>
                    </a>
                    <figcaption class="figure-caption text-center">${timePart}</figcaption>
                </div>
            </div>
        `;

        this.galleryContainer.appendChild(col);
    });

    // Inicializar FS Lightbox después de un breve delay
    setTimeout(() => {
        if (typeof refreshFsLightbox === 'function') {
            refreshFsLightbox();
        }
    }, 100);

    // Añadir controles de navegación si no existen
    this.addNavigationControls();
}

    addNavigationControls() {
        // Eliminar controles existentes
        const existingControls = document.getElementById('gallery-navigation-controls');
        if (existingControls) {
            existingControls.remove();
        }

        // Crear controles de navegación
        const controls = document.createElement('div');
        controls.id = 'gallery-navigation-controls';
        controls.className = 'navigation-controls';
        controls.innerHTML = `
            <button id="prev-gallery-button" title="Imagen anterior">
                <i class="fas fa-chevron-left"></i>
            </button>
            <button id="play-gallery-button" title="Iniciar slideshow">
                <i class="fas fa-play"></i>
            </button>
            <button id="stop-gallery-button" title="Detener slideshow" style="display: none;">
                <i class="fas fa-stop"></i>
            </button>
            <button id="next-gallery-button" title="Siguiente imagen">
                <i class="fas fa-chevron-right"></i>
            </button>
        `;

        document.body.appendChild(controls);

        // Añadir event listeners
        setTimeout(() => {
            const prevButton = document.getElementById('prev-gallery-button');
            const nextButton = document.getElementById('next-gallery-button');
            const playButton = document.getElementById('play-gallery-button');
            const stopButton = document.getElementById('stop-gallery-button');

            if (prevButton) prevButton.addEventListener('click', () => this.prevImage());
            if (nextButton) nextButton.addEventListener('click', () => this.nextImage());
            if (playButton) playButton.addEventListener('click', () => this.startSlideshow());
            if (stopButton) stopButton.addEventListener('click', () => this.stopSlideshow());
        }, 100);
    }

    nextImage() {
        if (this.imageUrls.length === 0) return;

        if (this.currentImageIndex < this.imageUrls.length - 1) {
            this.currentImageIndex++;
        } else {
            this.currentImageIndex = 0; // Volver al inicio
        }

        // Abrir la siguiente imagen con FS Lightbox
        this.openWithFSLightbox(this.currentImageIndex);
    }

    prevImage() {
        if (this.imageUrls.length === 0) return;

        if (this.currentImageIndex > 0) {
            this.currentImageIndex--;
        } else {
            this.currentImageIndex = this.imageUrls.length - 1; // Ir al final
        }

        // Abrir la imagen anterior con FS Lightbox
        this.openWithFSLightbox(this.currentImageIndex);
    }

    openWithFSLightbox(index) {
        // Encontrar el elemento <a> correspondiente y hacer clic en él
        const galleryLinks = document.querySelectorAll('[data-fslightbox="gallery"]');
        if (galleryLinks && galleryLinks[index]) {
            galleryLinks[index].click();
        }
    }

    startSlideshow() {
        // Buscar botones en el DOM
        const playButton = document.getElementById('play-gallery-button');
        const stopButton = document.getElementById('stop-gallery-button');

        // Si existen, cambiar su visibilidad
        if (playButton && stopButton) {
            playButton.style.display = 'none';
            stopButton.style.display = 'inline-block';
        }

        // Iniciar intervalo
        this.slideshowInterval = setInterval(() => {
            this.nextImage();
        }, 2000); // Cambiar cada 2 segundos
    }

    stopSlideshow() {
        // Buscar botones en el DOM
        const playButton = document.getElementById('play-gallery-button');
        const stopButton = document.getElementById('stop-gallery-button');

        // Si existen, cambiar su visibilidad
        if (playButton && stopButton) {
            playButton.style.display = 'inline-block';
            stopButton.style.display = 'none';
        }

        // Detener intervalo
        if (this.slideshowInterval) {
            clearInterval(this.slideshowInterval);
            this.slideshowInterval = null;
        }
    }

    cleanupGallery() {
        // Limpiar intervalo de slideshow
        this.stopSlideshow();

        // Limpiar contenedor de galería si existe
        if (this.galleryContainer) {
            this.galleryContainer.innerHTML = '';
        }

        // Eliminar controles de navegación
        const controls = document.getElementById('gallery-navigation-controls');
        if (controls) {
            controls.remove();
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
            this.cleanupGallery();
            this.showLoading('Cargando imágenes...');

            // Simular carga asíncrona
            await new Promise(resolve => setTimeout(resolve, 100));

            this.createImageGallery();

            if (this.loadingElement) {
                this.loadingElement.style.display = 'none';
            }

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
document.addEventListener('DOMContentLoaded', function () {
    // Inicializar Litepicker primero
    initLitepicker();

    const form = document.getElementById('data-form');
    const plotArea = document.getElementById('plot-area');
    const plotTitle = document.getElementById('plot-title');
    const loadingIndicator = document.getElementById('loading');

    if (form) {
        form.addEventListener('submit', async function (e) {
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
                    varLabel: data.var_label,
                    imageUrls: data.image_urls,
                    simulationDate: data.simulation_date,
                    count: data.count
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