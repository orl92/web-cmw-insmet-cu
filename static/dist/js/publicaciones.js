// publicaciones.js - Visor de PDF Fullscreen Responsive
class PDFViewer {
    constructor() {
        this.pdfDoc = null;
        this.pageNum = 1;
        this.pageRendering = false;
        this.pageNumPending = null;
        this.currentScale = 1.0;
        this.autoScale = true;

        this.canvas = document.getElementById('pdfCanvas');
        this.ctx = this.canvas.getContext('2d');
        this.modal = document.getElementById('pdfModal');

        this.init();
    }

    init() {
        // Configurar PDF.js worker usando la variable global
        if (typeof window.PDFJS_WORKER_SRC !== 'undefined') {
            pdfjsLib.GlobalWorkerOptions.workerSrc = window.PDFJS_WORKER_SRC;
        } else {
            console.error('PDFJS_WORKER_SRC no está definida');
            return;
        }

        // Event listeners para los botones de navegación
        document.getElementById('prevPage').addEventListener('click', () => this.onPrevPage());
        document.getElementById('nextPage').addEventListener('click', () => this.onNextPage());

        // Event listener para el selector de zoom
        document.getElementById('zoomSelect').addEventListener('change', (e) => {
            this.onZoomChange(e.target.value);
        });

        // Manejar la apertura del modal para visualizar PDF
        this.bindPdfButtons();

        // Manejar redimensionamiento de ventana
        window.addEventListener('resize', () => this.onWindowResize());

        // Cerrar modal con ESC
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.modal.style.display === 'block') {
                this.hideModal();
            }
        });
    }

    // Mostrar modal
    showModal() {
        this.modal.style.display = 'block';
        document.body.style.overflow = 'hidden'; // Prevenir scroll del body
    }

    // Ocultar modal
    hideModal() {
        this.modal.style.display = 'none';
        document.body.style.overflow = ''; // Restaurar scroll del body
        this.cleanup();
    }

    // Calcular escala automática basada en el tamaño del contenedor
    calculateAutoScale(viewport, container) {
        const containerWidth = container.clientWidth - 40; // Margen para padding
        const containerHeight = container.clientHeight - 80; // Más espacio para controles

        const scaleX = containerWidth / viewport.width;
        const scaleY = containerHeight / viewport.height;

        // Usar la escala más pequeña para asegurar que el PDF quepa completamente
        return Math.min(scaleX, scaleY, 1.5); // Máximo 150% para mantener legibilidad
    }

    // Función para renderizar una página
    renderPage(num) {
        this.pageRendering = true;

        this.pdfDoc.getPage(num).then((page) => {
            // Obtener viewport a escala 1.0 para calcular
            const viewport = page.getViewport({ scale: 1.0 });

            // Calcular escala
            let scale;
            if (this.autoScale) {
                const container = document.getElementById('pdfContainer');
                scale = this.calculateAutoScale(viewport, container);
            } else {
                scale = this.currentScale;
            }

            // Aplicar escala
            const scaledViewport = page.getViewport({ scale });

            // Configurar canvas con alta resolución para dispositivos retina
            const pixelRatio = window.devicePixelRatio || 1;
            this.canvas.height = scaledViewport.height * pixelRatio;
            this.canvas.width = scaledViewport.width * pixelRatio;
            this.canvas.style.height = `${scaledViewport.height}px`;
            this.canvas.style.width = `${scaledViewport.width}px`;

            const renderContext = {
                canvasContext: this.ctx,
                viewport: scaledViewport,
                transform: [pixelRatio, 0, 0, pixelRatio, 0, 0]
            };

            const renderTask = page.render(renderContext);

            renderTask.promise.then(() => {
                this.pageRendering = false;

                if (this.pageNumPending !== null) {
                    this.renderPage(this.pageNumPending);
                    this.pageNumPending = null;
                }

                document.getElementById('pageNum').textContent = num;

                // Scroll al top cuando cambia de página
                document.getElementById('pdfContainer').scrollTop = 0;
            });
        });

        document.getElementById('pageCount').textContent = this.pdfDoc.numPages;
    }

    // Función para navegar a la siguiente página
    queueRenderPage(num) {
        if (this.pageRendering) {
            this.pageNumPending = num;
        } else {
            this.renderPage(num);
        }
    }

    // Función para mostrar la página anterior
    onPrevPage() {
        if (this.pageNum <= 1) {
            return;
        }
        this.pageNum--;
        this.queueRenderPage(this.pageNum);
    }

    // Función para mostrar la siguiente página
    onNextPage() {
        if (this.pageNum >= this.pdfDoc.numPages) {
            return;
        }
        this.pageNum++;
        this.queueRenderPage(this.pageNum);
    }

    // Manejar cambio de zoom
    onZoomChange(zoomValue) {
        if (zoomValue === 'auto') {
            this.autoScale = true;
            this.currentScale = 1.0;
        } else {
            this.autoScale = false;
            this.currentScale = parseFloat(zoomValue);
        }

        if (this.pdfDoc) {
            this.renderPage(this.pageNum);
        }
    }

    // Manejar redimensionamiento de ventana
    onWindowResize() {
        if (this.pdfDoc && this.autoScale && this.modal.style.display === 'block') {
            // Re-renderizar con nueva escala automática
            this.renderPage(this.pageNum);
        }
    }

    // Vincular botones de PDF
    bindPdfButtons() {
        document.querySelectorAll('.view-pdf-btn').forEach(button => {
            button.addEventListener('click', (e) => {
                const pdfUrl = e.currentTarget.getAttribute('data-pdf-url');
                const pdfTitle = e.currentTarget.getAttribute('data-pdf-title');
                this.openPdfModal(pdfUrl, pdfTitle);
            });
        });
    }

    // Abrir modal de PDF
    openPdfModal(pdfUrl, pdfTitle) {
        // Actualizar título del modal
        document.getElementById('pdfModalLabel').textContent = pdfTitle;

        // Actualizar enlace de descarga
        document.getElementById('downloadPdf').href = pdfUrl;

        // Resetear a escala automática
        document.getElementById('zoomSelect').value = 'auto';
        this.autoScale = true;
        this.currentScale = 1.0;
        this.pageNum = 1;

        // Mostrar mensaje de carga
        const pdfContainer = document.getElementById('pdfContainer');
        pdfContainer.innerHTML = `
            <div style="display: flex; justify-content: center; align-items: center; height: 100%; width: 100%;">
                <div style="text-align: center;">
                    <div style="border: 4px solid #f3f3f3; border-top: 4px solid #007bff; border-radius: 50%; width: 50px; height: 50px; animation: spin 1s linear infinite; margin: 0 auto;"></div>
                    <p style="margin-top: 1rem; color: #6c757d;">Cargando PDF...</p>
                </div>
            </div>
            <style>
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
            </style>
        `;

        // Mostrar el modal inmediatamente
        this.showModal();

        // Cargar el PDF
        pdfjsLib.getDocument(pdfUrl).promise.then((pdfDoc_) => {
            this.pdfDoc = pdfDoc_;

            // Restaurar contenido original del contenedor
            pdfContainer.innerHTML = '<canvas id="pdfCanvas" style="box-shadow: 0 2px 10px rgba(0,0,0,0.1); background-color: white;"></canvas>';
            this.canvas = document.getElementById('pdfCanvas');
            this.ctx = this.canvas.getContext('2d');

            // Renderizar la primera página
            this.renderPage(this.pageNum);

        }).catch((error) => {
            console.error('Error al cargar el PDF:', error);

            // Mostrar error
            pdfContainer.innerHTML = `
                <div style="display: flex; justify-content: center; align-items: center; height: 100%; width: 100%;">
                    <div style="text-align: center; color: #dc3545;">
                        <div style="font-size: 3rem; margin-bottom: 1rem;">❌</div>
                        <h4 style="margin-bottom: 1rem;">Error al cargar el PDF</h4>
                        <p style="margin-bottom: 1.5rem;">No se pudo cargar el documento. Por favor, intente nuevamente.</p>
                        <button onclick="PDFViewerInstance.hideModal()" style="padding: 0.5rem 1.5rem; background-color: #6c757d; color: white; border: none; border-radius: 4px; cursor: pointer;">
                            Cerrar
                        </button>
                    </div>
                </div>
            `;
        });
    }

    // Limpiar cuando se cierra el modal
    cleanup() {
        if (this.ctx && this.canvas) {
            this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        }
        this.pdfDoc = null;
        this.pageNum = 1;
        this.currentScale = 1.0;
        this.autoScale = true;
    }
}

// Crear instancia global
let PDFViewerInstance;

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    PDFViewerInstance = new PDFViewer();
});