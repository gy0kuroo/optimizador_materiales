/**
 * Diálogos modales centrados (confirmar / avisos) — CutLess.
 * Requiere Bootstrap 5 (bundle) y el elemento #cutlessModalDialogo en el DOM.
 */
(function () {
    'use strict';

    window.cutlessConfirmar = function (options) {
        options = options || {};
        return new Promise(function (resolve) {
            var el = document.getElementById('cutlessModalDialogo');
            if (!el || typeof bootstrap === 'undefined') {
                resolve(window.confirm(options.mensaje || options.titulo || '¿Confirmar?'));
                return;
            }

            var tituloEl = el.querySelector('#cutlessModalDialogoTitulo');
            var cuerpoEl = el.querySelector('#cutlessModalDialogoCuerpo');
            var btnOk = el.querySelector('#cutlessModalDialogoOk');
            var btnCancel = el.querySelector('#cutlessModalDialogoCancel');
            var btnClose = el.querySelector('#cutlessModalDialogoClose');

            tituloEl.textContent = options.titulo || '¿Confirmar?';
            cuerpoEl.textContent = options.mensaje || '';
            btnOk.textContent = options.textoAceptar || 'Aceptar';
            btnCancel.textContent = options.textoCancelar || 'Cancelar';
            var destructiva = options.destructiva === true;
            btnOk.classList.toggle('btn-danger', destructiva);
            btnOk.classList.toggle('btn-primary', !destructiva);
            btnOk.dataset.action = destructiva ? 'delete' : 'primary';

            var soloAceptar = options.soloAceptar === true;
            if (soloAceptar) {
                btnCancel.classList.add('d-none');
            } else {
                btnCancel.classList.remove('d-none');
            }

            var modal = bootstrap.Modal.getOrCreateInstance(el, {
                backdrop: 'static',
                keyboard: true
            });

            var accepted = false;

            function onHidden() {
                el.removeEventListener('shown.bs.modal', onShown);
                el.removeEventListener('hidden.bs.modal', onHidden);
                btnOk.removeEventListener('click', onOk);
                btnCancel.removeEventListener('click', onCancel);
                if (btnClose) {
                    btnClose.removeEventListener('click', onClose);
                }
                resolve(accepted);
            }

            function onShown() {
                // Cancelar recibe el foco en una acción irreversible.
                (destructiva && !soloAceptar ? btnCancel : btnOk).focus();
            }

            function onOk() {
                accepted = true;
                modal.hide();
            }

            function onCancel() {
                accepted = false;
                modal.hide();
            }

            function onClose() {
                accepted = false;
                modal.hide();
            }

            el.addEventListener('hidden.bs.modal', onHidden);
            el.addEventListener('shown.bs.modal', onShown);
            btnOk.addEventListener('click', onOk);
            if (!soloAceptar) {
                btnCancel.addEventListener('click', onCancel);
            }
            if (btnClose) {
                btnClose.addEventListener('click', onClose);
            }

            modal.show();
        });
    };

    window.cutlessAlerta = function (options) {
        options = options || {};
        return window.cutlessConfirmar({
            titulo: options.titulo || 'Aviso',
            mensaje: options.mensaje || '',
            textoAceptar: options.textoAceptar || 'Aceptar',
            soloAceptar: true
        });
    };
})();
