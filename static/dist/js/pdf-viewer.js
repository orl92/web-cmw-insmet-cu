class PDFViewer {
    constructor(options) {
        this.pdfUrl = options.pdfUrl;
        this.modalPdfUrl = options.modalPdfUrl;

        // Variables globales para ambos visores
        this.cardPdfDoc = null;
        this.modalPdfDoc = null;
        this.modalCurrentPage = 1;
        this.modalCurrentScale = 1.0;
        this.cardCurrentScale = 1.0;
        
        // Variables para zoom y pan táctil
        this.initialDistance = null;
        this.lastScale = 1;
        this.isZooming = false;
        this.isPanning = false;
        this.touchStartX = 0;
        this.touchStartY = 0;
        this.lastTouchTime = 0;
        this.startScrollLeft = 0;
        this.startScrollTop = 0;
        
        // Calidad de renderizado
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
        
        return {
            sx: pixelRatio,
            sy: pixelRatio,
            scaled: pixelRatio !== 1
        };
    }

    // Función para renderizar una página con alta calidad
    renderPageWithQuality(page, scale, canvas, isModal = false) {
        const viewport = page.getViewport({ scale: scale });
        const context = canvas.getContext('2d', { alpha: false });

        // Mejorar la calidad para todos los dispositivos
        const outputScale = this.getOutputScale(context);
        
        // Calcular dimensiones reales del canvas
        const actualWidth = Math.floor(viewport.width * outputScale.sx);
        const actualHeight = Math.floor(viewport.height * outputScale.sy);
        
        canvas.width = actualWidth;
        canvas.height = actualHeight;
        
        // Dimensiones de visualización (CSS)
        const displayWidth = Math.floor(viewport.width);
        const displayHeight = Math.floor(viewport.height);
        
        canvas.style.width = displayWidth + 'px';
        canvas.style.height = displayHeight + 'px';

        const transform = outputScale.scaled ?
            [outputScale.sx, 0, 0, outputScale.sy, 0, 0] :
            null;

        const renderContext = {
            canvasContext: context,
            viewport: viewport,
            transform: transform,
            intent: 'display'
        };

        return page.render(renderContext).promise;
    }

    // Calcular escala para ajustar al ancho del contenedor
    calculateFitWidthScale(page) {
        const container = document.getElementById('pdfPreviewContainer');
        if (!container) return 1.0;
        
        const viewport = page.getViewport({ scale: 1 });
        const containerWidth = container.clientWidth - 40; // Padding
        
        return containerWidth / viewport.width;
    }

    // Función para renderizar todas las páginas en el visor de la tarjeta
    renderAllCardPages() {
        const pagesContainer = document.getElementById('pdfPages');

        if (!this.cardPdfDoc) return;

        pagesContainer.innerHTML = '';

        // Renderizar todas las páginas
        for (let pageNum = 1; pageNum <= this.cardPdfDoc.numPages; pageNum++) {
            this.cardPdfDoc.getPage(pageNum).then((page) => {
                // Calcular escala para esta página
                const fitScale = this.calculateFitWidthScale(page);
                const scale = fitScale * this.cardCurrentScale;

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
        
        if (pageInfo) {
            pageInfo.textContent = `Página ${pageNum} de ${this.modalPdfDoc.numPages}`;
        }
        
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

        if (prevBtn && this.modalPdfDoc) {
            prevBtn.disabled = this.modalCurrentPage <= 1;
        }
        if (nextBtn && this.modalPdfDoc) {
            nextBtn.disabled = this.modalCurrentPage >= this.modalPdfDoc.numPages;
        }
    }

    // Ajustar al ancho en la vista previa móvil
    fitToWidth() {
        this.cardCurrentScale = 1.0;
        this.renderAllCardPages();
        this.showZoomIndicator(Math.round(this.cardCurrentScale * 100) + '%');
    }

    // Ajustar al ancho en el modal
    modalFitToWidth() {
        if (!this.modalPdfDoc) return;

        this.modalPdfDoc.getPage(1).then((page) => {
            const viewport = page.getViewport({ scale: 1 });
            const containerWidth = window.innerWidth - 80;
            this.modalCurrentScale = containerWidth / viewport.width;
            this.renderModalPage(this.modalCurrentPage);
        });
    }

    // Mostrar indicador de zoom
    showZoomIndicator(text) {
        let indicator = document.getElementById('zoomIndicator');
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = 'zoomIndicator';
            indicator.className = 'zoom-indicator';
            document.getElementById('pdfPreviewContainer').appendChild(indicator);
        }
        
        indicator.textContent = text;
        indicator.classList.add('show');
        
        setTimeout(() => {
            indicator.classList.remove('show');
        }, 2000);
    }

    // Manejar gestos táctiles para zoom y pan
    handleTouchStart(e) {
        const pdfContainer = document.getElementById('pdfPreviewContainer');
        
        if (e.touches.length === 2) {
            e.preventDefault();
            this.isZooming = true;
            this.isPanning = false;
            this.initialDistance = Math.hypot(
                e.touches[0].clientX - e.touches[1].clientX,
                e.touches[0].clientY - e.touches[1].clientY
            );
            this.lastScale = this.cardCurrentScale;
        } else if (e.touches.length === 1 && this.cardCurrentScale > 1.0) {
            // Solo permitir pan si hay zoom
            this.isPanning = true;
            this.isZooming = false;
            this.touchStartX = e.touches[0].clientX;
            this.touchStartY = e.touches[0].clientY;
            this.startScrollLeft = pdfContainer.scrollLeft;
            this.startScrollTop = pdfContainer.scrollTop;
        }
    }

    handleTouchMove(e) {
        const pdfContainer = document.getElementById('pdfPreviewContainer');
        
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
                
                // Mostrar indicador de zoom
                this.showZoomIndicator(Math.round(this.cardCurrentScale * 100) + '%');
            }
        } else if (e.touches.length === 1 && this.isPanning && this.cardCurrentScale > 1.0) {
            e.preventDefault();
            
            const deltaX = this.touchStartX - e.touches[0].clientX;
            const deltaY = this.touchStartY - e.touches[0].clientY;
            
            pdfContainer.scrollLeft = this.startScrollLeft + deltaX;
            pdfContainer.scrollTop = this.startScrollTop + deltaY;
        }
    }

    handleTouchEnd(e) {
        if (e.touches.length < 2) {
            this.isZooming = false;
            this.initialDistance = null;
        }
        if (e.touches.length === 0) {
            this.isPanning = false;
        }
    }

    // Doble tap para resetear zoom
    handleDoubleTap(e) {
        const currentTime = new Date().getTime();
        const tapLength = currentTime - this.lastTouchTime;
        
        if (tapLength < 300 && tapLength > 0) {
            e.preventDefault();
            
            if (this.cardCurrentScale !== 1.0) {
                this.cardCurrentScale = 1.0;
                // Resetear scroll al centro
                const pdfContainer = document.getElementById('pdfPreviewContainer');
                if (pdfContainer) {
                    pdfContainer.scrollLeft = 0;
                    pdfContainer.scrollTop = 0;
                }
            } else {
                this.cardCurrentScale = 1.5;
            }
            
            this.renderAllCardPages();
            this.showZoomIndicator(Math.round(this.cardCurrentScale * 100) + '%');
        }
        
        this.lastTouchTime = currentTime;
    }

    // Redimensionar al cambiar tamaño de ventana
    handleResize() {
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
            pagesContainer.innerHTML = '<div class="pdf-loading-message">Cargando PDF...</div>';
        }

        pdfjsLib.getDocument(this.pdfUrl).promise.then((pdf) => {
            this.cardPdfDoc = pdf;
            this.cardCurrentScale = 1.0;
            this.renderAllCardPages();

            // Configurar eventos táctiles para el contenedor
            const pdfContainer = document.getElementById('pdfPreviewContainer');
            if (pdfContainer) {
                // Prevenir zoom nativo del navegador durante gestos de pellizco
                pdfContainer.addEventListener('touchmove', (e) => {
                    if (e.scale !== 1) {
                        e.preventDefault();
                    }
                }, { passive: false });

                // Doble tap para zoom
                pdfContainer.addEventListener('touchend', (e) => this.handleDoubleTap(e));
                
                // Mejorar la experiencia táctil
                pdfContainer.style.cursor = 'grab';
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
        if (!pdfModal) return;

        pdfModal.addEventListener('show.bs.modal', (event) => {
            const button = event.relatedTarget;
            const pdfUrl = button ? button.getAttribute('data-pdf-url') : this.modalPdfUrl;

            if (pdfUrl) {
                // Cargar PDF para el modal
                pdfjsLib.getDocument(pdfUrl).promise.then((pdf) => {
                    this.modalPdfDoc = pdf;
                    this.modalCurrentPage = 1;
                    this.modalCurrentScale = 1.0;
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
        const prevBtn = document.getElementById('modalPrevPage');
        const nextBtn = document.getElementById('modalNextPage');
        const zoomOutBtn = document.getElementById('modalZoomOut');
        const zoomInBtn = document.getElementById('modalZoomIn');
        const fitWidthBtn = document.getElementById('modalFitWidth');

        if (prevBtn) {
            prevBtn.addEventListener('click', () => {
                if (this.modalCurrentPage > 1) {
                    this.modalCurrentPage--;
                    this.renderModalPage(this.modalCurrentPage);
                }
            });
        }

        if (nextBtn) {
            nextBtn.addEventListener('click', () => {
                if (this.modalPdfDoc && this.modalCurrentPage < this.modalPdfDoc.numPages) {
                    this.modalCurrentPage++;
                    this.renderModalPage(this.modalCurrentPage);
                }
            });
        }

        if (zoomOutBtn) {
            zoomOutBtn.addEventListener('click', () => {
                if (this.modalCurrentScale > 0.5) {
                    this.modalCurrentScale -= 0.2;
                    this.renderModalPage(this.modalCurrentPage);
                }
            });
        }

        if (zoomInBtn) {
            zoomInBtn.addEventListener('click', () => {
                if (this.modalCurrentScale < 3) {
                    this.modalCurrentScale += 0.2;
                    this.renderModalPage(this.modalCurrentPage);
                }
            });
        }

        if (fitWidthBtn) {
            fitWidthBtn.addEventListener('click', () => this.modalFitToWidth());
        }

        // Limpiar cuando se cierre el modal
        pdfModal.addEventListener('hidden.bs.modal', () => {
            this.modalPdfDoc = null;
            this.modalCurrentPage = 1;
            this.modalCurrentScale = 1.0;
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
        const pdfContainer = document.getElementById('pdfPreviewContainer');
        if (pdfContainer) {
            pdfContainer.addEventListener('touchstart', (e) => this.handleTouchStart(e));
            pdfContainer.addEventListener('touchmove', (e) => this.handleTouchMove(e));
            pdfContainer.addEventListener('touchend', (e) => this.handleTouchEnd(e));
        }
    }
}