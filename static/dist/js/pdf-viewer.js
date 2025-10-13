class PDFViewer {
    constructor(options) {
        this.pdfUrl = options.pdfUrl;
        this.modalPdfUrl = options.modalPdfUrl;

        // IDs personalizables para múltiples instancias
        this.containerId = options.containerId || 'pdfPreviewContainer';
        this.pagesId = options.pagesId || 'pdfPages';

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

        // Control para evitar múltiples inicializaciones del modal
        this.modalInitialized = false;
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
        const container = document.getElementById(this.containerId);
        if (!container) return 1.0;
        
        const viewport = page.getViewport({ scale: 1 });
        const containerWidth = container.clientWidth - 40; // Padding
        
        return containerWidth / viewport.width;
    }

    // Función para renderizar todas las páginas en el visor de la tarjeta
    renderAllCardPages() {
        const pagesContainer = document.getElementById(this.pagesId);

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

        // Limpiar contenedor antes de renderizar
        if (pagesContainer) {
            pagesContainer.innerHTML = '';
        }
        
        if (pageInfo) {
            pageInfo.textContent = `Página ${pageNum} de ${this.modalPdfDoc.numPages}`;
        }
        
        if (zoomLevel) {
            zoomLevel.textContent = Math.round(this.modalCurrentScale * 100) + '%';
        }

        this.modalPdfDoc.getPage(pageNum).then((page) => {
            const canvas = document.createElement('canvas');
            canvas.className = 'modal-pdf-canvas';
            canvas.setAttribute('data-page-number', pageNum);

            if (pagesContainer) {
                pagesContainer.appendChild(canvas);
            }

            // Renderizar con alta calidad
            this.renderPageWithQuality(page, this.modalCurrentScale, canvas, true);

            this.updateModalNavigation();
        }).catch(error => {
            console.error(`Error rendering modal page ${pageNum}:`, error);
            const pagesContainer = document.getElementById('modalPdfPages');
            if (pagesContainer) {
                pagesContainer.innerHTML = '<div class="pdf-error-message">Error al renderizar la página</div>';
            }
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
        const container = document.getElementById(this.containerId);
        if (!container) return;

        let indicator = container.querySelector('.zoom-indicator');
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.className = 'zoom-indicator';
            container.appendChild(indicator);
        }
        
        indicator.textContent = text;
        indicator.classList.add('show');
        
        setTimeout(() => {
            indicator.classList.remove('show');
        }, 2000);
    }

    // Manejar gestos táctiles para zoom y pan
    handleTouchStart(e) {
        const pdfContainer = document.getElementById(this.containerId);
        if (!pdfContainer) return;
        
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
        const pdfContainer = document.getElementById(this.containerId);
        if (!pdfContainer) return;
        
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
                const pdfContainer = document.getElementById(this.containerId);
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
        const pagesContainer = document.getElementById(this.pagesId);
        if (pagesContainer) {
            pagesContainer.innerHTML = '<div class="pdf-loading-message">Cargando PDF...</div>';
        }

        pdfjsLib.getDocument(this.pdfUrl).promise.then((pdf) => {
            this.cardPdfDoc = pdf;
            this.cardCurrentScale = 1.0;
            this.renderAllCardPages();

            // Configurar eventos táctiles para el contenedor
            const pdfContainer = document.getElementById(this.containerId);
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
            const pagesContainer = document.getElementById(this.pagesId);
            if (pagesContainer) {
                pagesContainer.innerHTML = '<div class="pdf-error-message">Error al cargar el PDF</div>';
            }
        });
    }

    // Manejar el modal - CORREGIDO para evitar múltiples inicializaciones
    setupModal() {
        // Si el modal ya fue inicializado, salir
        if (this.modalInitialized) {
            return;
        }

        const pdfModal = document.getElementById('pdfModal');
        if (!pdfModal) return;

        // Marcar como inicializado
        this.modalInitialized = true;

        // Usar una closure para mantener la referencia a esta instancia
        const instance = this;

        // Remover event listeners previos para evitar duplicados
        pdfModal.removeEventListener('show.bs.modal', this.modalShowHandler);
        pdfModal.removeEventListener('hidden.bs.modal', this.modalHideHandler);

        // Definir los handlers
        this.modalShowHandler = function(event) {
            const button = event.relatedTarget;
            const pdfUrl = button ? button.getAttribute('data-pdf-url') : instance.modalPdfUrl;

            if (pdfUrl) {
                // Limpiar PDF anterior
                if (instance.modalPdfDoc) {
                    instance.modalPdfDoc.destroy();
                    instance.modalPdfDoc = null;
                }

                // Limpiar contenedor
                const pagesContainer = document.getElementById('modalPdfPages');
                if (pagesContainer) {
                    pagesContainer.innerHTML = '<div class="pdf-loading-message">Cargando PDF...</div>';
                }

                // Cargar PDF para el modal
                pdfjsLib.getDocument(pdfUrl).promise.then((pdf) => {
                    instance.modalPdfDoc = pdf;
                    instance.modalCurrentPage = 1;
                    instance.modalCurrentScale = 1.0;
                    instance.renderModalPage(instance.modalCurrentPage);
                }).catch((error) => {
                    console.error('Error al cargar el PDF en el modal:', error);
                    const pagesContainer = document.getElementById('modalPdfPages');
                    if (pagesContainer) {
                        pagesContainer.innerHTML = '<div class="pdf-error-message">Error al cargar el PDF</div>';
                    }
                });
            }
        };

        this.modalHideHandler = function() {
            // Limpiar cuando se cierre el modal
            if (instance.modalPdfDoc) {
                instance.modalPdfDoc.destroy();
                instance.modalPdfDoc = null;
            }
            instance.modalCurrentPage = 1;
            instance.modalCurrentScale = 1.0;
            const pagesContainer = document.getElementById('modalPdfPages');
            if (pagesContainer) {
                pagesContainer.innerHTML = '';
            }
        };

        // Agregar event listeners
        pdfModal.addEventListener('show.bs.modal', this.modalShowHandler);
        pdfModal.addEventListener('hidden.bs.modal', this.modalHideHandler);

        // Event listeners para controles del modal
        this.setupModalControls();
    }

    // Configurar controles del modal
    setupModalControls() {
        const prevBtn = document.getElementById('modalPrevPage');
        const nextBtn = document.getElementById('modalNextPage');
        const zoomOutBtn = document.getElementById('modalZoomOut');
        const zoomInBtn = document.getElementById('modalZoomIn');
        const fitWidthBtn = document.getElementById('modalFitWidth');

        // Remover event listeners previos
        if (prevBtn) prevBtn.replaceWith(prevBtn.cloneNode(true));
        if (nextBtn) nextBtn.replaceWith(nextBtn.cloneNode(true));
        if (zoomOutBtn) zoomOutBtn.replaceWith(zoomOutBtn.cloneNode(true));
        if (zoomInBtn) zoomInBtn.replaceWith(zoomInBtn.cloneNode(true));
        if (fitWidthBtn) fitWidthBtn.replaceWith(fitWidthBtn.cloneNode(true));

        // Obtener referencias frescas después del clone
        const freshPrevBtn = document.getElementById('modalPrevPage');
        const freshNextBtn = document.getElementById('modalNextPage');
        const freshZoomOutBtn = document.getElementById('modalZoomOut');
        const freshZoomInBtn = document.getElementById('modalZoomIn');
        const freshFitWidthBtn = document.getElementById('modalFitWidth');

        if (freshPrevBtn) {
            freshPrevBtn.addEventListener('click', () => {
                if (this.modalCurrentPage > 1) {
                    this.modalCurrentPage--;
                    this.renderModalPage(this.modalCurrentPage);
                }
            });
        }

        if (freshNextBtn) {
            freshNextBtn.addEventListener('click', () => {
                if (this.modalPdfDoc && this.modalCurrentPage < this.modalPdfDoc.numPages) {
                    this.modalCurrentPage++;
                    this.renderModalPage(this.modalCurrentPage);
                }
            });
        }

        if (freshZoomOutBtn) {
            freshZoomOutBtn.addEventListener('click', () => {
                if (this.modalCurrentScale > 0.5) {
                    this.modalCurrentScale -= 0.2;
                    this.renderModalPage(this.modalCurrentPage);
                }
            });
        }

        if (freshZoomInBtn) {
            freshZoomInBtn.addEventListener('click', () => {
                if (this.modalCurrentScale < 3) {
                    this.modalCurrentScale += 0.2;
                    this.renderModalPage(this.modalCurrentPage);
                }
            });
        }

        if (freshFitWidthBtn) {
            freshFitWidthBtn.addEventListener('click', () => this.modalFitToWidth());
        }
    }

    // Inicializar todo
    init() {
        this.loadCardPDF();
        this.setupModal();

        // Agregar listener para redimensionamiento
        window.addEventListener('resize', () => this.handleResize());

        // Configurar gestos táctiles globales
        const pdfContainer = document.getElementById(this.containerId);
        if (pdfContainer) {
            // Remover event listeners previos
            pdfContainer.removeEventListener('touchstart', this.touchStartHandler);
            pdfContainer.removeEventListener('touchmove', this.touchMoveHandler);
            pdfContainer.removeEventListener('touchend', this.touchEndHandler);

            // Definir handlers
            this.touchStartHandler = (e) => this.handleTouchStart(e);
            this.touchMoveHandler = (e) => this.handleTouchMove(e);
            this.touchEndHandler = (e) => this.handleTouchEnd(e);

            // Agregar event listeners
            pdfContainer.addEventListener('touchstart', this.touchStartHandler);
            pdfContainer.addEventListener('touchmove', this.touchMoveHandler);
            pdfContainer.addEventListener('touchend', this.touchEndHandler);
        }
    }
}

// Inicialización global para evitar conflictos
let globalPDFViewerInitialized = false;

function initializePDFViewers() {
    // Evitar inicialización múltiple
    if (globalPDFViewerInitialized) {
        return;
    }
    globalPDFViewerInitialized = true;

    // Inicializar visor principal si existe
    const mainContainer = document.getElementById('pdfPreviewContainer');
    if (mainContainer) {
        const pdfUrl = mainContainer.getAttribute('data-pdf-url') || '';
        const viewer = new PDFViewer({
            pdfUrl: pdfUrl,
            modalPdfUrl: pdfUrl
        });
        viewer.init();
    }

    // Para avisos.html - inicializar múltiples instancias
    const warningContainers = document.querySelectorAll('[id^="pdfPreviewContainer-"]');
    warningContainers.forEach(container => {
        const idSuffix = container.id.replace('pdfPreviewContainer-', '');
        const pdfUrl = container.getAttribute('data-pdf-url');
        
        if (pdfUrl) {
            const warningViewer = new PDFViewer({
                pdfUrl: pdfUrl,
                modalPdfUrl: pdfUrl,
                containerId: `pdfPreviewContainer-${idSuffix}`,
                pagesId: `pdfPages-${idSuffix}`
            });
            warningViewer.init();
        }
    });
}

// Auto-inicialización cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializePDFViewers);
} else {
    initializePDFViewers();
}