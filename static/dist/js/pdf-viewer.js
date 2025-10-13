class PDFViewer {
    constructor(options) {
        this.pdfUrl = options.pdfUrl;
        this.modalPdfUrl = options.modalPdfUrl;

        // Variables globales para ambos visores
        this.cardPdfDoc = null;
        this.modalPdfDoc = null;
        this.modalCurrentPage = 1;
        this.modalCurrentScale = 1.5;
        this.cardCurrentScale = 1.0;
        this.initialDistance = null;
    }

    // Función para mejorar la calidad del renderizado
    getOutputScale(ctx) {
        const devicePixelRatio = window.devicePixelRatio || 1;
        const backingStoreRatio = ctx.webkitBackingStorePixelRatio ||
                                ctx.mozBackingStorePixelRatio ||
                                ctx.msBackingStorePixelRatio ||
                                ctx.oBackingStorePixelRatio ||
                                ctx.backingStorePixelRatio || 1;
        const pixelRatio = devicePixelRatio / backingStoreRatio;
        return {
            sx: pixelRatio,
            sy: pixelRatio,
            scaled: pixelRatio !== 1
        };
    }

    // Función para renderizar una página con alta calidad
    renderPageWithQuality(page, scale, canvas) {
        const viewport = page.getViewport({ scale: scale });
        const context = canvas.getContext('2d');

        // Mejorar la calidad para dispositivos móviles
        const outputScale = this.getOutputScale(context);
        canvas.width = Math.floor(viewport.width * outputScale.sx);
        canvas.height = Math.floor(viewport.height * outputScale.sy);
        canvas.style.width = Math.floor(viewport.width) + 'px';
        canvas.style.height = Math.floor(viewport.height) + 'px';

        const transform = outputScale.scaled ?
            [outputScale.sx, 0, 0, outputScale.sy, 0, 0] :
            null;

        const renderContext = {
            canvasContext: context,
            viewport: viewport,
            transform: transform
        };

        return page.render(renderContext).promise;
    }

    // Función para calcular el ancho del contenedor
    getContainerWidth() {
        const container = document.getElementById('pdfPreviewContainer');
        if (!container) return 0;

        if (window.innerWidth <= 768) {
            return container.clientWidth - 20;
        }
        return container.clientWidth - 20;
    }

    // Función para renderizar todas las páginas en el visor de la tarjeta
    renderAllCardPages() {
        const pagesContainer = document.getElementById('pdfPages');
        const zoomLevel = document.getElementById('mobileZoomLevel');

        if (!this.cardPdfDoc) return;

        pagesContainer.innerHTML = '';

        // Actualizar nivel de zoom
        if (zoomLevel) {
            zoomLevel.textContent = Math.round(this.cardCurrentScale * 100) + '%';
        }

        // Ancho disponible para cada página
        const containerWidth = this.getContainerWidth();

        // Renderizar todas las páginas
        for (let pageNum = 1; pageNum <= this.cardPdfDoc.numPages; pageNum++) {
            this.cardPdfDoc.getPage(pageNum).then((page) => {
                const viewport = page.getViewport({ scale: 1 });
                const scale = (containerWidth / viewport.width) * this.cardCurrentScale;
                const scaledViewport = page.getViewport({ scale: scale });

                const canvas = document.createElement('canvas');
                canvas.className = 'pdf-page-canvas';

                pagesContainer.appendChild(canvas);

                // Renderizar con alta calidad
                this.renderPageWithQuality(page, scale, canvas);
            });
        }
    }

    // Función para renderizar una página en el modal
    renderModalPage(pageNum) {
        const pagesContainer = document.getElementById('modalPdfPages');
        const pageInfo = document.getElementById('modalPageInfo');
        const zoomLevel = document.getElementById('modalZoomLevel');

        if (!this.modalPdfDoc) return;

        pagesContainer.innerHTML = '';
        pageInfo.textContent = `Página ${pageNum} de ${this.modalPdfDoc.numPages}`;

        if (zoomLevel) {
            zoomLevel.textContent = Math.round(this.modalCurrentScale * 100) + '%';
        }

        this.modalPdfDoc.getPage(pageNum).then((page) => {
            const viewport = page.getViewport({ scale: this.modalCurrentScale });

            const canvas = document.createElement('canvas');
            canvas.className = 'modal-pdf-canvas';

            pagesContainer.appendChild(canvas);

            // Renderizar con alta calidad
            this.renderPageWithQuality(page, this.modalCurrentScale, canvas);

            this.updateModalNavigation();
        });
    }

    // Funciones de navegación para el modal
    updateModalNavigation() {
        const prevBtn = document.getElementById('modalPrevPage');
        const nextBtn = document.getElementById('modalNextPage');

        if (prevBtn) prevBtn.disabled = this.modalCurrentPage <= 1;
        if (nextBtn) nextBtn.disabled = this.modalCurrentPage >= this.modalPdfDoc.numPages;
    }

    // Ajustar al ancho en la vista previa móvil
    fitToWidth() {
        this.cardCurrentScale = 1.0;
        this.renderAllCardPages();
    }

    // Ajustar al ancho en el modal
    modalFitToWidth() {
        if (!this.modalPdfDoc) return;

        this.modalPdfDoc.getPage(1).then((page) => {
            const viewport = page.getViewport({ scale: 1 });
            const containerWidth = window.innerWidth - 80; // Considerar padding
            this.modalCurrentScale = containerWidth / viewport.width;
            this.renderModalPage(this.modalCurrentPage);
        });
    }

    // Redimensionar al cambiar tamaño de ventana
    handleResize() {
        // Mostrar/ocultar controles móviles según el tamaño de pantalla
        const mobileControls = document.querySelector('.mobile-pdf-controls');
        if (mobileControls) {
            if (window.innerWidth <= 768) {
                mobileControls.classList.remove('d-none');
            } else {
                mobileControls.classList.add('d-none');
            }
        }

        if (this.cardPdfDoc) {
            this.renderAllCardPages();
        }
        if (this.modalPdfDoc) {
            this.renderModalPage(this.modalCurrentPage);
        }
    }

    // Manejar gestos táctiles
    handleTouchStart(e) {
        if (e.touches.length === 2) {
            this.initialDistance = Math.hypot(
                e.touches[0].clientX - e.touches[1].clientX,
                e.touches[0].clientY - e.touches[1].clientY
            );
        }
    }

    handleTouchMove(e) {
        if (e.touches.length === 2 && this.initialDistance !== null) {
            e.preventDefault();
            const currentDistance = Math.hypot(
                e.touches[0].clientX - e.touches[1].clientX,
                e.touches[0].clientY - e.touches[1].clientY
            );

            const zoomContainer = document.getElementById('pdfPreviewContainer');
            if (zoomContainer && zoomContainer.contains(e.target)) {
                const zoomFactor = currentDistance / this.initialDistance;
                if (zoomFactor > 1.1) {
                    this.cardCurrentScale += 0.1;
                    this.renderAllCardPages();
                    this.initialDistance = currentDistance;
                } else if (zoomFactor < 0.9) {
                    if (this.cardCurrentScale > 0.5) {
                        this.cardCurrentScale -= 0.1;
                        this.renderAllCardPages();
                        this.initialDistance = currentDistance;
                    }
                }
            }
        }
    }

    handleTouchEnd() {
        this.initialDistance = null;
    }

    // Cargar PDF en la tarjeta principal
    loadCardPDF() {
        if (!this.pdfUrl) return;

        pdfjsLib.getDocument(this.pdfUrl).promise.then((pdf) => {
            this.cardPdfDoc = pdf;
            this.renderAllCardPages();

            // Configurar controles de zoom para móvil
            const mobileZoomIn = document.getElementById('mobileZoomIn');
            const mobileZoomOut = document.getElementById('mobileZoomOut');
            const mobileFitWidth = document.getElementById('mobileFitWidth');

            if (mobileZoomIn) {
                mobileZoomIn.addEventListener('click', () => {
                    this.cardCurrentScale += 0.2;
                    this.renderAllCardPages();
                });
            }

            if (mobileZoomOut) {
                mobileZoomOut.addEventListener('click', () => {
                    if (this.cardCurrentScale > 0.5) {
                        this.cardCurrentScale -= 0.2;
                        this.renderAllCardPages();
                    }
                });
            }

            if (mobileFitWidth) {
                mobileFitWidth.addEventListener('click', () => this.fitToWidth());
            }

        }).catch((error) => {
            console.error('Error al cargar el PDF:', error);
            const pagesContainer = document.getElementById('pdfPages');
            if (pagesContainer) {
                pagesContainer.innerHTML = '<div class="pdf-error-message">Error al cargar el PDF</div>';
            }
        });
    }

    // Manejar el modal
    setupModal() {
        const pdfModal = document.getElementById('pdfModal');

        pdfModal.addEventListener('show.bs.modal', (event) => {
            const button = event.relatedTarget;
            if (!button) return;

            const pdfUrl = button.getAttribute('data-pdf-url') || this.modalPdfUrl;

            if (pdfUrl) {
                // Cargar PDF para el modal
                pdfjsLib.getDocument(pdfUrl).promise.then((pdf) => {
                    this.modalPdfDoc = pdf;
                    this.modalCurrentPage = 1;
                    this.modalCurrentScale = window.innerWidth <= 768 ? 1.0 : 1.5;
                    this.renderModalPage(this.modalCurrentPage);
                }).catch((error) => {
                    console.error('Error al cargar el PDF en el modal:', error);
                    const pagesContainer = document.getElementById('modalPdfPages');
                    if (pagesContainer) {
                        pagesContainer.innerHTML = '<div class="pdf-error-message">Error al cargar el PDF</div>';
                    }
                });
            }
        });

        // Event listeners para controles del modal
        document.getElementById('modalPrevPage').addEventListener('click', () => {
            if (this.modalCurrentPage > 1) {
                this.modalCurrentPage--;
                this.renderModalPage(this.modalCurrentPage);
            }
        });

        document.getElementById('modalNextPage').addEventListener('click', () => {
            if (this.modalCurrentPage < this.modalPdfDoc.numPages) {
                this.modalCurrentPage++;
                this.renderModalPage(this.modalCurrentPage);
            }
        });

        document.getElementById('modalZoomOut').addEventListener('click', () => {
            if (this.modalCurrentScale > 0.5) {
                this.modalCurrentScale -= 0.2;
                this.renderModalPage(this.modalCurrentPage);
            }
        });

        document.getElementById('modalZoomIn').addEventListener('click', () => {
            this.modalCurrentScale += 0.2;
            this.renderModalPage(this.modalCurrentPage);
        });

        document.getElementById('modalFitWidth').addEventListener('click', () => this.modalFitToWidth());

        // Limpiar cuando se cierre el modal
        pdfModal.addEventListener('hidden.bs.modal', () => {
            this.modalPdfDoc = null;
            this.modalCurrentPage = 1;
            this.modalCurrentScale = window.innerWidth <= 768 ? 1.0 : 1.5;
            const pagesContainer = document.getElementById('modalPdfPages');
            if (pagesContainer) {
                pagesContainer.innerHTML = '';
            }
        });
    }

    // Inicializar todo
    init() {
        this.loadCardPDF();
        this.setupModal();

        // Agregar listener para redimensionamiento
        window.addEventListener('resize', () => this.handleResize());

        // Inicializar controles móviles
        this.handleResize();

        // Configurar gestos táctiles
        document.addEventListener('touchstart', (e) => this.handleTouchStart(e));
        document.addEventListener('touchmove', (e) => this.handleTouchMove(e));
        document.addEventListener('touchend', () => this.handleTouchEnd());
    }
}