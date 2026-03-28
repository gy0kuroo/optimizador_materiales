/**
 * Utilidades para confirmaciones y mejoras de UX
 */

// Asegurar que las funciones estén disponibles globalmente inmediatamente
(function() {
    'use strict';
    
    // Confirmación mejorada para eliminaciones
    window.confirmarEliminacion = function(mensaje, tipo) {
        tipo = tipo || 'optimización';
        const mensajes = {
            'optimización': '¿Estás seguro de que deseas eliminar esta optimización? Esta acción no se puede deshacer.',
            'material': '¿Estás seguro de que deseas eliminar este material? Esta acción no se puede deshacer.',
            'cliente': '¿Estás seguro de que deseas eliminar este cliente? Esta acción no se puede deshacer.',
            'proyecto': '¿Estás seguro de que deseas eliminar este proyecto? Esta acción no se puede deshacer.',
            'plantilla': '¿Estás seguro de que deseas eliminar esta plantilla? Esta acción no se puede deshacer.',
        };
        
        const mensajeFinal = mensaje || mensajes[tipo] || '¿Estás seguro de que deseas realizar esta acción?';
        return confirm(mensajeFinal);
    };
    
    // Indicador de carga para generación de PDFs/gráficos
    window.mostrarIndicadorCarga = function(mensaje) {
        mensaje = mensaje || 'Generando...';
        // Si ya hay un overlay activo, eliminarlo antes de crear nuevo
        window.ocultarIndicadorCarga();

        // Crear overlay de carga
        const overlay = document.createElement('div');
        overlay.id = 'loading-overlay';
        overlay.style.cssText = 
            'position: fixed;' +
            'top: 0;' +
            'left: 0;' +
            'width: 100%;' +
            'height: 100%;' +
            'background: rgba(0, 0, 0, 0.7);' +
            'display: flex;' +
            'justify-content: center;' +
            'align-items: center;' +
            'z-index: 9999;' +
            'flex-direction: column;';
        
        const spinner = document.createElement('div');
        spinner.className = 'spinner-border text-light';
        spinner.style.cssText = 'width: 3rem; height: 3rem;';
        spinner.setAttribute('role', 'status');
        
        const texto = document.createElement('div');
        texto.className = 'text-light mt-3';
        texto.style.cssText = 'font-size: 1.2rem;';
        texto.textContent = mensaje;
        
        overlay.appendChild(spinner);
        overlay.appendChild(texto);
        document.body.appendChild(overlay);

        // Autoocultar para evitar que la UI quede bloqueada en caso de descargas con attachment
        if (window._loadingOverlayTimeoutId) {
            clearTimeout(window._loadingOverlayTimeoutId);
        }
        window._loadingOverlayTimeoutId = setTimeout(function() {
            window.ocultarIndicadorCarga();
        }, 15000); // 15 segundos
        
        return overlay;
    };
    
    window.ocultarIndicadorCarga = function() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.remove();
        }
        if (window._loadingOverlayTimeoutId) {
            clearTimeout(window._loadingOverlayTimeoutId);
            window._loadingOverlayTimeoutId = null;
        }
    };

    window.obtenerNombreArchivoDesdeDisposition = function(contentDisposition, fallback) {
        if (!contentDisposition) {
            return fallback;
        }
        const filenameMatch = /filename\*=UTF-8''([^;]*)/.exec(contentDisposition) || /filename="?([^";]+)"?/.exec(contentDisposition);
        if (filenameMatch && filenameMatch[1]) {
            try {
                return decodeURIComponent(filenameMatch[1]);
            } catch (e) {
                return filenameMatch[1];
            }
        }
        return fallback;
    };

    window.descargarArchivo = async function(url, mensaje) {
        try {
            window.mostrarIndicadorCarga(mensaje || 'Generando archivo... Por favor espera.');
            const response = await fetch(url, {
                method: 'GET',
                credentials: 'same-origin'
            });

            if (!response.ok) {
                throw new Error('Error en la descarga: ' + response.status + ' ' + response.statusText);
            }

            const blob = await response.blob();
            const contentDisposition = response.headers.get('content-disposition');
            const nombreSugerido = window.obtenerNombreArchivoDesdeDisposition(contentDisposition, url.split('/').pop().split('?')[0]);
            const enlace = document.createElement('a');
            const objectUrl = URL.createObjectURL(blob);
            enlace.href = objectUrl;
            enlace.download = nombreSugerido || 'descarga';
            document.body.appendChild(enlace);
            enlace.click();
            enlace.remove();
            URL.revokeObjectURL(objectUrl);
        } catch (error) {
            console.error(error);
            alert('No se pudo descargar el archivo. Intenta de nuevo.');
        } finally {
            window.ocultarIndicadorCarga();
        }
    };
})();

// Agregar confirmación a todos los formularios de eliminación
document.addEventListener('DOMContentLoaded', function() {
    // Formularios de eliminación en historial
    const deleteForms = document.querySelectorAll('form.delete-form-inline, form[action*="borrar"], form[action*="eliminar"]');
    deleteForms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            const tipo = this.getAttribute('data-tipo') || 'optimización';
            if (!window.confirmarEliminacion(null, tipo)) {
                e.preventDefault();
                return false;
            }
        });
    });
    
    // Botones de eliminar en páginas de confirmación
    const deleteButtons = document.querySelectorAll('button.btn-danger[type="submit"]');
    deleteButtons.forEach(function(button) {
        const form = button.closest('form');
        if (form && form.action && form.action.includes('eliminar')) {
            button.addEventListener('click', function(e) {
                const tipo = this.getAttribute('data-tipo') || 'optimización';
                if (!window.confirmarEliminacion(null, tipo)) {
                    e.preventDefault();
                    form.onsubmit = function() { return false; };
                    return false;
                }
            });
        }
    });
    
    // Agregar descarga por AJAX para evitar que el overlay quede bloqueado
    const descargaLinks = document.querySelectorAll(
        'a[href*="descargar_pdf"], a[href*="descargar_excel"], a[href*="descargar_png"], a[href$=".pdf"], a[href$=".xlsx"], a[href$=".xls"]'
    );
    descargaLinks.forEach(function(link) {
        // No interceptar el botón de imprimir (abre vista previa / nueva ventana)
        if (link.href.includes('imprimir_plan_corte') || link.target === '_blank') {
            return;
        }

        // Evitar doble manejo si ya está configurado
        if (!link.dataset.descargaAjax) {
            link.dataset.descargaAjax = 'true';
            link.addEventListener('click', function(event) {
                event.preventDefault();
                const mensaje = this.dataset.cargaTexto || 'Descargando archivo... Por favor espera.';
                window.descargarArchivo(this.href, mensaje);
            });
        }
    });
    
    // Formularios que generan PDFs/gráficos (solo si no tienen onsubmit ya definido)
    const generateForms = document.querySelectorAll('form[action*="index"], form[action*="optimizar"]');
    generateForms.forEach(function(form) {
        // Solo agregar si no tiene onsubmit ya definido
        if (!form.getAttribute('onsubmit')) {
            form.addEventListener('submit', function() {
                window.mostrarIndicadorCarga('Procesando optimización... Esto puede tardar unos segundos.');
            });
        }
    });
});

