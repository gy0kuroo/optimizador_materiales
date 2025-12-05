// Gestión de timeout de sesión por inactividad
(function() {
    'use strict';
    
    let inactivityTimer;
    let warningTimer;
    let warningShown = false;
    let timeoutSeconds = null;
    let warningSeconds = 60; // Mostrar advertencia 1 minuto antes
    
    // Obtener timeout desde el atributo data del body o usar valor por defecto
    function initializeTimeout() {
        const body = document.body;
        const timeoutAttr = body.getAttribute('data-session-timeout');
        
        if (timeoutAttr && timeoutAttr !== 'null' && timeoutAttr !== '0') {
            timeoutSeconds = parseInt(timeoutAttr);
            // Mostrar advertencia 1 minuto antes o 10% del tiempo, lo que sea menor
            warningSeconds = Math.min(60, Math.floor(timeoutSeconds * 0.1));
        } else {
            // Si está desactivado (0) o no configurado, no hacer nada
            return;
        }
        
        if (timeoutSeconds > 0) {
            startInactivityTimer();
        }
    }
    
    // Eventos que indican actividad del usuario
    const activityEvents = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'];
    
    // Reiniciar el timer cuando hay actividad
    function resetTimer() {
        if (timeoutSeconds === null || timeoutSeconds === 0) return;
        
        clearTimeout(inactivityTimer);
        clearTimeout(warningTimer);
        warningShown = false;
        
        // Ocultar advertencia si está visible
        const warningModal = document.getElementById('session-warning-modal');
        if (warningModal) {
            const bsModal = bootstrap.Modal.getInstance(warningModal);
            if (bsModal) {
                bsModal.hide();
            }
        }
        
        startInactivityTimer();
    }
    
    // Iniciar el timer de inactividad
    function startInactivityTimer() {
        if (timeoutSeconds === null || timeoutSeconds === 0) return;
        
        const warningTime = (timeoutSeconds - warningSeconds) * 1000;
        const logoutTime = timeoutSeconds * 1000;
        
        // Timer para mostrar advertencia
        if (warningTime > 0) {
            warningTimer = setTimeout(function() {
                showWarning();
            }, warningTime);
        }
        
        // Timer para cerrar sesión
        inactivityTimer = setTimeout(function() {
            logout();
        }, logoutTime);
    }
    
    // Mostrar advertencia de que la sesión está por expirar
    function showWarning() {
        if (warningShown) return;
        warningShown = true;
        
        const minutes = Math.floor(warningSeconds / 60);
        const seconds = warningSeconds % 60;
        const timeText = minutes > 0 ? `${minutes} min ${seconds} seg` : `${seconds} segundos`;
        
        // Crear modal de advertencia si no existe
        let modal = document.getElementById('session-warning-modal');
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'session-warning-modal';
            modal.className = 'modal fade';
            modal.setAttribute('tabindex', '-1');
            modal.setAttribute('data-bs-backdrop', 'static');
            modal.setAttribute('data-bs-keyboard', 'false');
            modal.innerHTML = `
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content">
                        <div class="modal-header bg-warning">
                            <h5 class="modal-title">⏱️ Sesión por expirar</h5>
                        </div>
                        <div class="modal-body">
                            <p>Tu sesión expirará en <strong id="session-time-remaining">${timeText}</strong> debido a inactividad.</p>
                            <p>¿Deseas continuar trabajando?</p>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-primary" id="session-stay-active">
                                Continuar
                            </button>
                            <button type="button" class="btn btn-secondary" id="session-logout-now">
                                Cerrar sesión ahora
                            </button>
                        </div>
                    </div>
                </div>
            `;
            document.body.appendChild(modal);
        }
        
        // Actualizar tiempo restante
        const timeElement = document.getElementById('session-time-remaining');
        if (timeElement) {
            timeElement.textContent = timeText;
        }
        
        // Mostrar modal
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
        
        // Contador regresivo
        let remaining = warningSeconds;
        const countdown = setInterval(function() {
            remaining--;
            const minutes = Math.floor(remaining / 60);
            const seconds = remaining % 60;
            const timeText = minutes > 0 ? `${minutes} min ${seconds} seg` : `${seconds} segundos`;
            
            if (timeElement) {
                timeElement.textContent = timeText;
            }
            
            if (remaining <= 0) {
                clearInterval(countdown);
            }
        }, 1000);
        
        // Botón para continuar
        document.getElementById('session-stay-active').addEventListener('click', function() {
            clearInterval(countdown);
            bsModal.hide();
            resetTimer();
        });
        
        // Botón para cerrar sesión ahora
        document.getElementById('session-logout-now').addEventListener('click', function() {
            clearInterval(countdown);
            logout();
        });
    }
    
    // Cerrar sesión
    function logout() {
        // Limpiar timers
        clearTimeout(inactivityTimer);
        clearTimeout(warningTimer);
        
        // Redirigir a logout
        window.location.href = '/usuarios/logout/';
    }
    
    // Agregar listeners de actividad
    activityEvents.forEach(function(event) {
        document.addEventListener(event, resetTimer, true);
    });
    
    // Inicializar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeTimeout);
    } else {
        initializeTimeout();
    }
})();

