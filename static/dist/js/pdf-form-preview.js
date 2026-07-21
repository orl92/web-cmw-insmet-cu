// pdf-form-preview.js
class PDFFormPreview {
    constructor(fileInputId, previewContainerId) {
        this.fileInput = document.getElementById(fileInputId);
        this.previewContainer = document.getElementById(previewContainerId);
        this.currentPdfDoc = null;
        this.handleFileSelectBound = (e) => this.handleFileSelect(e);

        this.init();
    }

    init() {
        if (!this.fileInput || !this.previewContainer) {
            console.error('No se encontraron los elementos necesarios para la vista previa de PDF');
            return;
        }

        this.fileInput.addEventListener('change', this.handleFileSelectBound);

        // Mostrar estado inicial
        this.showInitialState();
    }

    handleFileSelect(e) {
        const file = e.target.files[0];

        if (file && file.type === 'application/pdf') {
            this.loadAndPreviewPDF(file);
        } else if (file) {
            this.showError('Por favor, selecciona un archivo PDF válido.');
        } else {
            this.showInitialState();
        }
    }

    loadAndPreviewPDF(file) {
        this.cleanupPreviousPdf();

        const fileReader = new FileReader();

        fileReader.onload = () => {
            if (typeof pdfjsLib === 'undefined') {
                this.showError('La librería PDF no está disponible. Recarga la página.');
                return;
            }
            const typedarray = new Uint8Array(fileReader.result);

            pdfjsLib.getDocument(typedarray).promise.then((pdf) => {
                this.currentPdfDoc = pdf;
                this.renderPDFPreview(pdf);
            }).catch((error) => {
                console.error('Error al cargar el PDF:', error);
                this.showError('Error al cargar el PDF.');
            });
        };

        fileReader.onerror = () => {
            this.showError('Error al leer el archivo.');
        };

        fileReader.readAsArrayBuffer(file);
    }

    renderPDFPreview(pdfDoc) {
        // Crear estructura de vista previa
        this.previewContainer.innerHTML = `
            <div class="pdf-preview-wrapper">
                <div class="pdf-preview-container">
                    <div class="pdf-pages-container"></div>
                </div>
            </div>
        `;

        const pagesContainer = this.previewContainer.querySelector('.pdf-pages-container');
        const container = this.previewContainer.querySelector('.pdf-preview-container');

        this.renderAllPages(pdfDoc, pagesContainer, container);
    }

    renderAllPages(pdfDoc, pagesContainer, container) {
        pagesContainer.innerHTML = '';

        const renderPromises = [];

        for (let pageNum = 1; pageNum <= pdfDoc.numPages; pageNum++) {
            const renderPromise = pdfDoc.getPage(pageNum).then((page) => {
                return this.renderPage(page, pagesContainer, container);
            });
            renderPromises.push(renderPromise);
        }

        Promise.all(renderPromises).catch((error) => {
            console.error('Error al renderizar el PDF:', error);
            this.showError('Error al renderizar el PDF.');
        });
    }

    renderPage(page, pagesContainer, container) {
        return new Promise((resolve, reject) => {
            const fitScale = this.calculateFitWidthScale(page, container);
            const viewport = page.getViewport({ scale: fitScale });

            const canvas = document.createElement('canvas');
            const context = canvas.getContext('2d');
            canvas.height = viewport.height;
            canvas.width = viewport.width;

            // Estilos del canvas
            canvas.className = 'pdf-preview-page';
            canvas.style.display = 'block';
            canvas.style.margin = '10px auto';

            pagesContainer.appendChild(canvas);

            // Renderizar la página
            const renderContext = {
                canvasContext: context,
                viewport: viewport
            };

            page.render(renderContext).promise.then(resolve).catch(reject);
        });
    }

    calculateFitWidthScale(page, container) {
        const viewport = page.getViewport({ scale: 1 });
        const containerWidth = container.clientWidth - 40; // Padding
        return containerWidth / viewport.width;
    }

    cleanupPreviousPdf() {
        if (this.currentPdfDoc) {
            this.currentPdfDoc.destroy();
            this.currentPdfDoc = null;
        }
    }

    showInitialState() {
        this.previewContainer.innerHTML = `
            <div class="pdf-preview-initial-state">
                <p class="text-muted">Selecciona un archivo PDF para previsualizarlo</p>
            </div>
        `;
    }

    showError(message) {
        this.previewContainer.innerHTML = `
            <div class="pdf-preview-error">
                <p class="text-danger">${message}</p>
            </div>
        `;
    }

    destroy() {
        this.cleanupPreviousPdf();
        if (this.fileInput) {
            this.fileInput.removeEventListener('change', this.handleFileSelectBound);
        }
    }
}

// Inicialización automática cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    // Buscar automáticamente elementos con data-pdf-preview
    const previewElements = document.querySelectorAll('[data-pdf-preview]');

    previewElements.forEach(element => {
        const fileInputId = element.getAttribute('data-file-input');
        const previewContainerId = element.getAttribute('data-preview-container');

        if (fileInputId && previewContainerId) {
            new PDFFormPreview(fileInputId, previewContainerId);
        }
    });
});