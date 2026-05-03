/**
 * Utilidades para confirmaciones y mejoras de UX
 */

(function () {
    'use strict';

    window.confirmarEliminacion = async function (mensaje, tipo) {
        tipo = tipo || 'optimización';
        var mensajes = {
            'optimización': '¿Estás seguro de que deseas eliminar esta optimización? Esta acción no se puede deshacer.',
            'material': '¿Estás seguro de que deseas eliminar este material? Esta acción no se puede deshacer.',
            'cliente': '¿Estás seguro de que deseas eliminar este cliente? Esta acción no se puede deshacer.',
            'proyecto': '¿Estás seguro de que deseas eliminar este proyecto? Esta acción no se puede deshacer.',
            'plantilla': '¿Estás seguro de que deseas eliminar esta plantilla? Esta acción no se puede deshacer.',
            'seleccion': '¿Estás seguro de que deseas borrar las optimizaciones seleccionadas? Esta acción no se puede deshacer.'
        };

        var mensajeFinal = mensaje || mensajes[tipo] || '¿Estás seguro de que deseas realizar esta acción?';
        if (typeof window.cutlessConfirmar !== 'function') {
            return window.confirm(mensajeFinal);
        }
        return window.cutlessConfirmar({
            titulo: 'Confirmar eliminación',
            mensaje: mensajeFinal,
            textoAceptar: 'Sí, eliminar',
            textoCancelar: 'Cancelar'
        });
    };

    window.mostrarIndicadorCarga = function (mensaje) {
        mensaje = mensaje || 'Generando...';
        window.ocultarIndicadorCarga();

        var overlay = document.createElement('div');
        overlay.id = 'loading-overlay';
        overlay.style.cssText =
            'position:fixed;top:0;left:0;width:100%;height:100%;' +
            'background:rgba(0,0,0,0.7);display:flex;justify-content:center;' +
            'align-items:center;z-index:9999;flex-direction:column;';

        var spinner = document.createElement('div');
        spinner.className = 'spinner-border text-light';
        spinner.style.cssText = 'width:3rem;height:3rem;';
        spinner.setAttribute('role', 'status');

        var texto = document.createElement('div');
        texto.className = 'text-light mt-3';
        texto.style.cssText = 'font-size:1.2rem;';
        texto.textContent = mensaje;

        overlay.appendChild(spinner);
        overlay.appendChild(texto);
        document.body.appendChild(overlay);

        if (window._loadingOverlayTimeoutId) {
            clearTimeout(window._loadingOverlayTimeoutId);
        }
        window._loadingOverlayTimeoutId = setTimeout(function () {
            window.ocultarIndicadorCarga();
        }, 15000);

        return overlay;
    };

    window.ocultarIndicadorCarga = function () {
        var overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.remove();
        }
        if (window._loadingOverlayTimeoutId) {
            clearTimeout(window._loadingOverlayTimeoutId);
            window._loadingOverlayTimeoutId = null;
        }
    };

    window.obtenerNombreArchivoDesdeDisposition = function (contentDisposition, fallback) {
        if (!contentDisposition) {
            return fallback;
        }
        var filenameMatch = /filename\*=UTF-8''([^;]*)/.exec(contentDisposition) || /filename="?([^";]+)"?/.exec(contentDisposition);
        if (filenameMatch && filenameMatch[1]) {
            try {
                return decodeURIComponent(filenameMatch[1]);
            } catch (e) {
                return filenameMatch[1];
            }
        }
        return fallback;
    };

    window.descargarArchivo = async function (url, mensaje) {
        try {
            window.mostrarIndicadorCarga(mensaje || 'Generando archivo... Por favor espera.');
            var response = await fetch(url, {
                method: 'GET',
                credentials: 'same-origin'
            });

            if (!response.ok) {
                throw new Error('Error en la descarga: ' + response.status + ' ' + response.statusText);
            }

            var blob = await response.blob();
            var contentDisposition = response.headers.get('content-disposition');
            var nombreSugerido = window.obtenerNombreArchivoDesdeDisposition(contentDisposition, url.split('/').pop().split('?')[0]);
            var enlace = document.createElement('a');
            var objectUrl = URL.createObjectURL(blob);
            enlace.href = objectUrl;
            enlace.download = nombreSugerido || 'descarga';
            document.body.appendChild(enlace);
            enlace.click();
            enlace.remove();
            URL.revokeObjectURL(objectUrl);
        } catch (error) {
            console.error(error);
            if (typeof window.cutlessAlerta === 'function') {
                await window.cutlessAlerta({
                    titulo: 'Error de descarga',
                    mensaje: 'No se pudo descargar el archivo. Intenta de nuevo.'
                });
            } else {
                alert('No se pudo descargar el archivo. Intenta de nuevo.');
            }
        } finally {
            window.ocultarIndicadorCarga();
        }
    };
})();

document.addEventListener('DOMContentLoaded', function () {
    var skipAttr = 'data-cutless-skip-confirm';

    function attachDeleteConfirm(form) {
        if (form.getAttribute('data-cutless-no-confirm') === '1') {
            return;
        }
        form.addEventListener('submit', async function (e) {
            if (form.getAttribute(skipAttr) === '1') {
                form.removeAttribute(skipAttr);
                return;
            }
            e.preventDefault();
            var customMsg = form.getAttribute('data-cutless-mensaje');
            var tipo = form.getAttribute('data-tipo') || 'optimización';
            var ok = await window.confirmarEliminacion(customMsg || null, tipo);
            if (ok) {
                form.setAttribute(skipAttr, '1');
                form.requestSubmit();
            }
        });
    }

    var deleteForms = document.querySelectorAll('form.delete-form-inline, form[action*="borrar"], form[action*="eliminar"]');
    deleteForms.forEach(attachDeleteConfirm);

    var descargaLinks = document.querySelectorAll(
        'a[href*="descargar_pdf"], a[href*="descargar_excel"], a[href*="descargar_png"], a[href$=".pdf"], a[href$=".xlsx"], a[href$=".xls"]'
    );
    descargaLinks.forEach(function (link) {
        if (link.href.includes('imprimir_plan_corte') || link.target === '_blank') {
            return;
        }
        if (!link.dataset.descargaAjax) {
            link.dataset.descargaAjax = 'true';
            link.addEventListener('click', function (event) {
                event.preventDefault();
                var mensaje = this.dataset.cargaTexto || 'Descargando archivo... Por favor espera.';
                window.descargarArchivo(this.href, mensaje);
            });
        }
    });

    var generateForms = document.querySelectorAll('form[action*="index"], form[action*="optimizar"]');
    generateForms.forEach(function (form) {
        if (!form.getAttribute('onsubmit')) {
            form.addEventListener('submit', function () {
                window.mostrarIndicadorCarga('Procesando optimización... Esto puede tardar unos segundos.');
            });
        }
    });
});
