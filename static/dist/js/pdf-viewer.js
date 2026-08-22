class PDFViewer {
    constructor(options) {
        // URLs
        this.pdfUrl = options.pdfUrl || '';
        this.modalPdfUrl = options.modalPdfUrl || '';

        // IDs personalizables
        this.containerId = options.containerId || 'pdfPreviewContainer';
        this.pagesId = options.pagesId || 'pdfPages';
        this.statusId = options.statusId || '';

        // IDs para modal (compartidos)
        this.modalPagesId = options.modalPagesId || 'modalPdfPages';
        this.modalPageInfoId = options.modalPageInfoId || 'modalPageInfo';
        this.modalZoomLevelId = options.modalZoomLevelId || 'modalZoomLevel';
        this.modalPrevPageId = options.modalPrevPageId || 'modalPrevPage';
        this.modalNextPageId = options.modalNextPageId || 'modalNextPage';
        this.modalZoomOutId = options.modalZoomOutId || 'modalZoomOut';
        this.modalZoomInId = options.modalZoomInId || 'modalZoomIn';
        this.modalFitWidthId = options.modalFitWidthId || 'modalFitWidth';

        // Variables de estado
        this.pdfDoc = null;
        this.currentPage = 1;
        this.currentScale = 1.0;
        this.isPreview = options.isPreview || false;
        this.isModal = options.isModal || false;

        // ID único para esta instancia
        this.instanceId = 'pdf-' + Math.random().toString(36).substr(2, 9);

        console.log('PDFViewer inicializado:', {
            instanceId: this.instanceId,
            containerId: this.containerId,
            isPreview: this.isPreview,
            isModal: this.isModal
        });
    }

    // Función para renderizar una página
    async renderPage(page, scale, container) {
        try {
            const viewport = page.getViewport({ scale: scale });

            // Crear canvas
            const canvas = document.createElement('canvas');
            const context = canvas.getContext('2d');

            // Configurar canvas
            canvas.height = viewport.height;
            canvas.width = viewport.width;
            canvas.className = this.isModal ? 'modal-pdf-canvas' : 'pdf-page-canvas';
            canvas.dataset.instanceId = this.instanceId;

            // Accesibilidad: el canvas es la representación visual de la página
            canvas.setAttribute('role', 'img');
            canvas.setAttribute('aria-label', `Página ${page.pageNumber} del documento`);

            // Estilos
            canvas.style.display = 'block';
            canvas.style.margin = '0 auto';
            canvas.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
            canvas.style.borderRadius = '4px';
            canvas.style.backgroundColor = 'white';

            if (this.isModal) {
                canvas.style.marginBottom = '20px';
            }

            console.log(`[${this.instanceId}] Renderizando - Tamaño: ${canvas.width}x${canvas.height}, Escala: ${scale}`);

            // Renderizar la página
            const renderContext = {
                canvasContext: context,
                viewport: viewport
            };

            await page.render(renderContext).promise;

            // Agregar al contenedor
            if (container) {
                container.innerHTML = '';
                container.appendChild(canvas);
            }

            return canvas;
        } catch (error) {
            console.error(`[${this.instanceId}] Error renderizando página:`, error);
            throw error;
        }
    }

    // Cargar PDF para vista previa o modal
    async loadPDF(isModal = false) {
        const url = isModal ? this.modalPdfUrl : this.pdfUrl;
        const pagesId = isModal ? this.modalPagesId : this.pagesId;
        const containerId = isModal ? null : this.containerId;

        if (!url) {
            console.log(`[${this.instanceId}] No hay URL de PDF`);
            return;
        }

        console.log(`[${this.instanceId}] Cargando PDF:`, url);

        try {
            // Mostrar indicador de carga
            const pagesContainer = document.getElementById(pagesId);
            if (pagesContainer) {
                pagesContainer.innerHTML = `
                    <div class="text-center py-4">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">Cargando...</span>
                        </div>
                        <p class="mt-2 text-muted">Cargando PDF...</p>
                    </div>
                `;
            }

            // Cargar el documento PDF
            const loadingTask = pdfjsLib.getDocument({
                url: url,
                withCredentials: true
            });

            this.pdfDoc = await loadingTask.promise;
            console.log(`[${this.instanceId}] PDF cargado: ${this.pdfDoc.numPages} páginas`);

            // Renderizar
            if (isModal) {
                await this.renderModalPage(1);
                if (!this.modalInitialized) {
                    this.setupModalControls();
                    this.modalInitialized = true;
                }
            } else {
                await this.renderPreview();
            }

        } catch (error) {
            console.error(`[${this.instanceId}] Error cargando PDF:`, error);
            const pagesContainer = document.getElementById(pagesId);
            if (pagesContainer) {
                pagesContainer.innerHTML = `
                    <div class="alert alert-danger text-center">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        Error al cargar el PDF
                        <br>
                        <small>${error.message}</small>
                    </div>
                `;
            }
        }
    }

    // Renderizar vista previa (solo primera página)
    async renderPreview() {
        if (!this.pdfDoc) return;

        const pagesContainer = document.getElementById(this.pagesId);
        if (!pagesContainer) return;

        try {
            // Obtener primera página
            const page = await this.pdfDoc.getPage(1);

            // Calcular escala para vista previa
            const container = document.getElementById(this.containerId);
            const containerWidth = container ? container.clientWidth - 40 : 400;
            const viewport = page.getViewport({ scale: 1 });
            const scale = Math.min(containerWidth / viewport.width, 1.5);

            // Renderizar
            await this.renderPage(page, scale, pagesContainer);

            // Mostrar información si hay más páginas
            if (this.pdfDoc.numPages > 1) {
                const pageInfo = document.createElement('div');
                pageInfo.className = 'text-center text-muted small mt-2';
                pageInfo.innerHTML = `<i class="fas fa-file-alt me-1"></i> ${this.pdfDoc.numPages} páginas en total`;
                pagesContainer.appendChild(pageInfo);
            }

        } catch (error) {
            console.error(`[${this.instanceId}] Error renderizando vista previa:`, error);
            throw error;
        }
    }

    // Renderizar página del modal
    async renderModalPage(pageNum) {
        if (!this.pdfDoc) return;

        const pagesContainer = document.getElementById(this.modalPagesId);
        const pageInfo = document.getElementById(this.modalPageInfoId);
        const zoomLevel = document.getElementById(this.modalZoomLevelId);

        if (!pagesContainer) return;

        try {
            // Actualizar información
            if (pageInfo) {
                pageInfo.textContent = `Página ${pageNum} de ${this.pdfDoc.numPages}`;
            }

            if (zoomLevel) {
                zoomLevel.textContent = `${Math.round(this.currentScale * 100)}%`;
            }

            // Obtener la página
            const page = await this.pdfDoc.getPage(pageNum);

            // Renderizar
            await this.renderPage(page, this.currentScale, pagesContainer);

            // Actualizar navegación
            this.updateModalNavigation();

        } catch (error) {
            console.error(`[${this.instanceId}] Error renderizando página modal:`, error);
            throw error;
        }
    }

    // Actualizar navegación del modal
    updateModalNavigation() {
        const prevBtn = document.getElementById(this.modalPrevPageId);
        const nextBtn = document.getElementById(this.modalNextPageId);

        if (prevBtn && this.pdfDoc) {
            prevBtn.disabled = this.currentPage <= 1;
        }
        if (nextBtn && this.pdfDoc) {
            nextBtn.disabled = this.currentPage >= this.pdfDoc.numPages;
        }
    }

    // Configurar controles del modal
    setupModalControls() {
        const instance = this;

        // Botón anterior
        const prevBtn = document.getElementById(this.modalPrevPageId);
        if (prevBtn) {
            prevBtn.addEventListener('click', function() {
                if (instance.pdfDoc && instance.currentPage > 1) {
                    instance.currentPage--;
                    instance.renderModalPage(instance.currentPage);
                }
            });
        }

        // Botón siguiente
        const nextBtn = document.getElementById(this.modalNextPageId);
        if (nextBtn) {
            nextBtn.addEventListener('click', function() {
                if (instance.pdfDoc && instance.currentPage < instance.pdfDoc.numPages) {
                    instance.currentPage++;
                    instance.renderModalPage(instance.currentPage);
                }
            });
        }

        // Zoom out
        const zoomOutBtn = document.getElementById(this.modalZoomOutId);
        if (zoomOutBtn) {
            zoomOutBtn.addEventListener('click', function() {
                if (instance.currentScale > 0.5) {
                    instance.currentScale = Math.max(0.5, instance.currentScale - 0.2);
                    instance.renderModalPage(instance.currentPage);
                }
            });
        }

        // Zoom in
        const zoomInBtn = document.getElementById(this.modalZoomInId);
        if (zoomInBtn) {
            zoomInBtn.addEventListener('click', function() {
                if (instance.currentScale < 3) {
                    instance.currentScale = Math.min(3, instance.currentScale + 0.2);
                    instance.renderModalPage(instance.currentPage);
                }
            });
        }

        // Ajustar al ancho
        const fitWidthBtn = document.getElementById(this.modalFitWidthId);
        if (fitWidthBtn) {
            fitWidthBtn.addEventListener('click', async function() {
                if (instance.pdfDoc) {
                    try {
                        const page = await instance.pdfDoc.getPage(1);
                        const viewport = page.getViewport({ scale: 1 });
                        const modalWidth = window.innerWidth - 100;
                        instance.currentScale = modalWidth / viewport.width;
                        await instance.renderModalPage(instance.currentPage);
                    } catch (error) {
                        console.error('Error ajustando al ancho:', error);
                    }
                }
            });
        }
    }

    // Inicializar
    async init() {
        console.log(`[${this.instanceId}] Inicializando...`);

        if (this.isModal) {
            // Para modal, solo configurar controles
            this.setupModalControls();
        } else {
            // Para vista previa, cargar PDF
            await this.loadPDF(false);
        }
    }

    // Cargar nuevo PDF en el modal
    async loadNewPDF(url, title = 'PDF') {
        this.modalPdfUrl = url;

        // Actualizar título del modal
        const modalTitle = document.getElementById('pdfModalLabel');
        if (modalTitle) {
            modalTitle.textContent = title;
        }

        // Actualizar el enlace de descarga con el PDF activo
        const downloadLink = document.getElementById('modalDownloadLink');
        if (downloadLink) {
            downloadLink.href = url;
        }

        // Resetear estado
        this.currentPage = 1;
        this.currentScale = 1.5;

        // Cargar PDF
        await this.loadPDF(true);
    }

    // Destruir instancia
    destroy() {
        if (this.pdfDoc) {
            this.pdfDoc.destroy();
            this.pdfDoc = null;
        }
        console.log(`[${this.instanceId}] Instancia destruida`);
    }
}

// Sistema de gestión de instancias
class PDFViewerManager {
    constructor() {
        this.viewers = {};
        this.modalViewer = null;
        this.modalInitialized = false;
    }

    // Crear visor para vista previa
    createPreviewViewer(containerId, pagesId, pdfUrl, statusId = '') {
        const viewer = new PDFViewer({
            pdfUrl: pdfUrl,
            containerId: containerId,
            pagesId: pagesId,
            statusId: statusId,
            isPreview: true
        });

        this.viewers[containerId] = viewer;
        viewer.init();

        return viewer;
    }

    // Crear o obtener visor para modal
    getModalViewer() {
        if (!this.modalViewer) {
            this.modalViewer = new PDFViewer({
                isModal: true,
                modalPagesId: 'modalPdfPages',
                modalPageInfoId: 'modalPageInfo',
                modalZoomLevelId: 'modalZoomLevel',
                modalPrevPageId: 'modalPrevPage',
                modalNextPageId: 'modalNextPage',
                modalZoomOutId: 'modalZoomOut',
                modalZoomInId: 'modalZoomIn',
                modalFitWidthId: 'modalFitWidth'
            });

            this.modalViewer.init();
            this.setupModalEvents();
        }

        return this.modalViewer;
    }

    // Configurar eventos del modal
    setupModalEvents() {
        const modal = document.getElementById('pdfModal');
        if (!modal || this.modalInitialized) return;

        const manager = this;

        // Cuando se muestra el modal
        modal.addEventListener('show.bs.modal', function(event) {
            const button = event.relatedTarget;
            const pdfUrl = button.getAttribute('data-pdf-url');
            const pdfTitle = button.getAttribute('data-pdf-title') || 'PDF';

            if (pdfUrl && manager.modalViewer) {
                manager.modalViewer.loadNewPDF(pdfUrl, pdfTitle);
            }
        });

        // Cuando se oculta el modal
        modal.addEventListener('hidden.bs.modal', function() {
            if (manager.modalViewer && manager.modalViewer.pdfDoc) {
                manager.modalViewer.destroy();
            }
        });

        this.modalInitialized = true;
    }

    // Inicializar todos los visores en la página
    initializeAll() {
        console.log('Inicializando todos los visores de PDF...');

        // Inicializar vista previa principal si existe
        const mainContainer = document.getElementById('pdfPreviewContainer');
        if (mainContainer) {
            const pdfUrl = mainContainer.getAttribute('data-pdf-url') || '';
            if (pdfUrl) {
                this.createPreviewViewer('pdfPreviewContainer', 'pdfPages', pdfUrl);
            }
        }

        // Inicializar visores de avisos
        const warningContainers = document.querySelectorAll('[id^="pdfPreviewContainer-"]');
        warningContainers.forEach(container => {
            const id = container.id;
            const pagesId = id.replace('pdfPreviewContainer', 'pdfPages');
            const pdfUrl = container.getAttribute('data-pdf-url');

            if (pdfUrl) {
                this.createPreviewViewer(id, pagesId, pdfUrl);
            }
        });

        // Inicializar modal
        this.getModalViewer();
    }
}

// Crear instancia global del manager
window.pdfViewerManager = new PDFViewerManager();

// Auto-inicialización
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.pdfViewerManager.initializeAll();
    });
} else {
    window.pdfViewerManager.initializeAll();
}

// Hacer las clases disponibles globalmente
window.PDFViewer = PDFViewer;
window.PDFViewerManager = PDFViewerManager;
