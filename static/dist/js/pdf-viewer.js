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
        
        // Variables para zoom táctil
        this.initialDistance = null;
        this.lastScale = 1;
        this.isZooming = false;
        this.touchStartX = 0;
        this.touchStartY = 0;
        
        // Mejorar calidad de renderizado
        this.renderQuality = window.devicePixelRatio || 1;
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
        
        // Aumentar calidad en dispositivos móviles
        const qualityMultiplier = window.innerWidth <= 768 ? 1.5 : 1;
        
        return {
            sx: pixelRatio * qualityMultiplier,
            sy: pixelRatio * qualityMultiplier,
            scaled: pixelRatio !== 1
        };
    }

    // Función para renderizar una página con alta calidad
    renderPageWithQuality(page, scale, canvas, isModal = false) {
        const viewport = page.getViewport({ scale: scale });
        const context = canvas.getContext('2d', { alpha: false });

        // Mejorar la calidad para todos los dispositivos
        const outputScale = this.getOutputScale(context);
        
        canvas.width = Math.floor(viewport.width * outputScale.sx);
        canvas.height = Math.floor(viewport.height * outputScale.sy);
        
        const displayWidth = Math.floor(viewport.width);
        const displayHeight = Math.floor(viewport.height);
        
        canvas.style.width = displayWidth + 'px';
        canvas.style.height = displayHeight + 'px';

        // Optimizar para móviles
        if (window.innerWidth <= 768) {
            canvas.style.maxWidth = '100%';
            canvas.style.height = 'auto';
        }

        const transform = outputScale.scaled ?
            [outputScale.sx, 0, 0, outputScale.sy, 0, 0] :
            null;

        const renderContext = {
            canvasContext: context,
            viewport: viewport,
            transform: transform,
            enableWebGL: true, // Habilitar WebGL si está disponible
            intent: 'display' // Mejorar calidad visual
        };

        return page.render(renderContext).promise;
    }

    // Función para calcular el ancho del contenedor
    getContainerWidth() {
        const container = document.getElementById('pdfPreviewContainer');
        if (!container) return 0;

        if (window.innerWidth <= 768) {
            return container.clientWidth - 10; // Menos padding en móviles
        }
        return container.clientWidth - 20;
    }

    // Función para renderizar todas las páginas en el visor de la tarjeta
    renderAllCardPages() {
        const pagesContainer = document.getElementById('pdfPages');

        if (!this.cardPdfDoc) return;

        pagesContainer.innerHTML = '';

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
                canvas.setAttribute('data-page-number', pageNum);

                pagesContainer.appendChild(canvas);

                // Renderizar con alta calidad
                this.renderPageWithQuality(page, scale, canvas, false);
            }).catch(error => {
                console.error(`Error rendering page ${pageNum}:`, error);
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
            canvas.setAttribute('data-page-number', pageNum);

            pagesContainer.appendChild(canvas);

            // Renderizar con alta calidad
            this.renderPageWithQuality(page, this.modalCurrentScale, canvas, true);

            this.updateModalNavigation();
        }).catch(error => {
            console.error(`Error rendering modal page ${pageNum}:`, error);
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
            const containerWidth = window.innerWidth - 40;
            this.modalCurrentScale = containerWidth / viewport.width;
            this.renderModalPage(this.modalCurrentPage);
        });
    }

    // Manejar gestos táctiles para zoom
    handleTouchStart(e) {
        if (e.touches.length === 2) {
            this.isZooming = true;
            this.initialDistance = Math.hypot(
                e.touches[0].clientX - e.touches[1].clientX,
                e.touches[0].clientY - e.touches[1].clientY
            );
            this.lastScale = this.cardCurrentScale;
            
            // Agregar clase para desactivar transiciones durante el zoom
            const pagesContainer = document.getElementById('pdfPages');
            if (pagesContainer) {
                pagesContainer.classList.add('zooming');
            }
        } else if (e.touches.length === 1) {
            this.touchStartX = e.touches[0].clientX;
            this.touchStartY = e.touches[0].clientY;
        }
    }

    handleTouchMove(e) {
        if (e.touches.length === 2 && this.isZooming) {
            e.preventDefault();
            
            const currentDistance = Math.hypot(
                e.touches[0].clientX - e.touches[1].clientX,
                e.touches[0].clientY - e.touches[1].clientY
            );

            if (this.initialDistance > 0) {
                const scaleFactor = currentDistance / this.initialDistance;
                const newScale = this.lastScale * scaleFactor;
                
                // Limitar zoom entre 0.5x y 3x
                this.cardCurrentScale = Math.max(0.5, Math.min(3, newScale));
                this.renderAllCardPages();
            }
        }
    }

    handleTouchEnd(e) {
        if (e.touches.length < 2) {
            this.isZooming = false;
            this.initialDistance = null;
            
            // Remover clase de zooming
            const pagesContainer = document.getElementById('pdfPages');
            if (pagesContainer) {
                setTimeout(() => {
                    pagesContainer.classList.remove('zooming');
                }, 100);
            }
        }
    }

    // Doble tap para resetear zoom
    handleDoubleTap(e) {
        if (this.cardCurrentScale !== 1.0) {
            this.cardCurrentScale = 1.0;
        } else {
            this.cardCurrentScale = 1.5;
        }
        this.renderAllCardPages();
    }

    // Redimensionar al cambiar tamaño de ventana
    handleResize() {
        // Usar debounce para evitar múltiples renderizados
        clearTimeout(this.resizeTimeout);
        this.resizeTimeout = setTimeout(() => {
            if (this.cardPdfDoc) {
                this.renderAllCardPages();
            }
            if (this.modalPdfDoc) {
                this.renderModalPage(this.modalCurrentPage);
            }
        }, 250);
    }

    // Cargar PDF en la tarjeta principal
    loadCardPDF() {
        if (!this.pdfUrl) return;

        // Mostrar indicador de carga
        const pagesContainer = document.getElementById('pdfPages');
        if (pagesContainer) {
            pagesContainer.innerHTML = '<div class="pdf-error-message">Cargando PDF...</div>';
        }

        pdfjsLib.getDocument({
            url: this.pdfUrl,
            cMapUrl: '../../node_modules/pdfjs-dist/cmaps/',
            cMapPacked: true
        }).promise.then((pdf) => {
            this.cardPdfDoc = pdf;
            this.renderAllCardPages();

            // Configurar eventos táctiles para el contenedor
            const pdfContainer = document.getElementById('pdfPreviewContainer');
            if (pdfContainer) {
                // Prevenir zoom nativo del navegador
                pdfContainer.addEventListener('touchmove', (e) => {
                    if (e.scale !== 1) {
                        e.preventDefault();
                    }
                }, { passive: false });

                // Doble tap para zoom
                let lastTap = 0;
                pdfContainer.addEventListener('touchend', (e) => {
                    const currentTime = new Date().getTime();
                    const tapLength = currentTime - lastTap;
                    if (tapLength < 500 && tapLength > 0) {
                        this.handleDoubleTap(e);
                    }
                    lastTap = currentTime;
                });
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
            const pdfUrl = button ? button.getAttribute('data-pdf-url') : this.modalPdfUrl;

            if (pdfUrl) {
                // Cargar PDF para el modal
                pdfjsLib.getDocument({
                    url: pdfUrl,
                    cMapUrl: '../../node_modules/pdfjs-dist/cmaps/',
                    cMapPacked: true
                }).promise.then((pdf) => {
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
            if (this.modalCurrentScale < 3) {
                this.modalCurrentScale += 0.2;
                this.renderModalPage(this.modalCurrentPage);
            }
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

        // Configurar gestos táctiles globales
        document.addEventListener('touchstart', (e) => this.handleTouchStart(e));
        document.addEventListener('touchmove', (e) => this.handleTouchMove(e));
        document.addEventListener('touchend', (e) => this.handleTouchEnd(e));
    }
}