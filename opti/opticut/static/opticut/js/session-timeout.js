// Gestión de timeout de sesión por inactividad
(function() {
    'use strict';
    
    let inactivityTimer;
    let warningTimer;
    let warningShown = false;
    let timeoutSeconds = null;
    let warningSeconds = 60; // Mostrar advertencia 1 minuto antes
    let countdownInterval = null;
    
    // Obtener timeout desde el atributo data del body o usar valor por defecto
    function initializeTimeout() {
        const body = document.body;
        if (!body) {
            console.warn('Session Timeout - Body no encontrado');
            return;
        }
        
        const timeoutAttr = body.getAttribute('data-session-timeout');
        
        // Debug: verificar que el atributo se esté leyendo correctamente (solo en desarrollo)
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            console.log('Session Timeout - Atributo data-session-timeout:', timeoutAttr);
        }
        
        // Verificar si el timeout está desactivado (0)
        if (timeoutAttr === '0' || timeoutAttr === 'null' || timeoutAttr === '') {
            // Si está desactivado (0) o no configurado, no hacer nada
            if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
                console.log('Session Timeout - Desactivado (timeout = 0). La sesión no se cerrará automáticamente.');
            }
            // No inicializar ningún timer
            timeoutSeconds = null;
            return;
        }
        
        // Si hay un valor válido, parsearlo y validarlo
        if (timeoutAttr) {
            timeoutSeconds = parseInt(timeoutAttr, 10);
            
            // Validar que sea un número válido y mayor que 0
            if (isNaN(timeoutSeconds) || timeoutSeconds <= 0) {
                if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
                    console.log('Session Timeout - Valor inválido, desactivando');
                }
                timeoutSeconds = null;
                return;
            }
            
            if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
                console.log('Session Timeout - Inicializado con', timeoutSeconds, 'segundos');
            }
            
            // Mostrar advertencia 1 minuto antes o 10% del tiempo, lo que sea menor
            warningSeconds = Math.min(60, Math.floor(timeoutSeconds * 0.1));
            
            // Iniciar el timer de inactividad
            startInactivityTimer();
        }
    }
    
    // Eventos que indican actividad del usuario
    const activityEvents = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'];
    
    // Reiniciar el timer cuando hay actividad
    function resetTimer() {
        if (timeoutSeconds === null || timeoutSeconds === 0) return;
        
        // Si la advertencia está mostrada, NO reiniciar automáticamente
        // Solo reiniciar cuando el usuario haga clic en "Continuar"
        if (warningShown) {
            return;
        }
        
        clearTimeout(inactivityTimer);
        clearTimeout(warningTimer);
        if (countdownInterval) {
            clearInterval(countdownInterval);
            countdownInterval = null;
        }
        warningShown = false;
        
        // Ocultar advertencia si está visible
        const warningModal = document.getElementById('session-warning-modal');
        if (warningModal) {
            const Bootstrap = typeof bootstrap !== 'undefined' ? bootstrap : (typeof window.bootstrap !== 'undefined' ? window.bootstrap : null);
            if (Bootstrap) {
                const bsModal = Bootstrap.Modal.getInstance(warningModal);
                if (bsModal) {
                    bsModal.hide();
                }
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
        // Si el timeout está desactivado, no mostrar advertencia
        if (timeoutSeconds === null || timeoutSeconds === 0) return;
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
        
        // Mostrar modal (usar bootstrap global o window.bootstrap)
        const Bootstrap = typeof bootstrap !== 'undefined' ? bootstrap : (typeof window.bootstrap !== 'undefined' ? window.bootstrap : null);
        if (!Bootstrap) {
            console.error('Session Timeout - Bootstrap no está disponible');
            return;
        }
        
        const bsModal = new Bootstrap.Modal(modal);
        bsModal.show();
        
        // Contador regresivo
        let remaining = warningSeconds;
        if (countdownInterval) {
            clearInterval(countdownInterval);
        }
        countdownInterval = setInterval(function() {
            remaining--;
            const minutes = Math.floor(remaining / 60);
            const seconds = remaining % 60;
            const timeText = minutes > 0 ? `${minutes} min ${seconds} seg` : `${seconds} segundos`;
            
            if (timeElement) {
                timeElement.textContent = timeText;
            }
            
            if (remaining <= 0) {
                clearInterval(countdownInterval);
                countdownInterval = null;
            }
        }, 1000);
    }
    
    // Cerrar sesión
    function logout() {
        // Limpiar timers
        clearTimeout(inactivityTimer);
        clearTimeout(warningTimer);
        if (countdownInterval) {
            clearInterval(countdownInterval);
            countdownInterval = null;
        }
        
        // Redirigir a logout
        window.location.href = '/usuarios/logout/';
    }
    
    // Agregar listeners de actividad
    activityEvents.forEach(function(event) {
        document.addEventListener(event, resetTimer, true);
    });
    
    // Agregar listeners del modal usando event delegation
    document.body.addEventListener('click', function(e) {
        if (e.target && e.target.id === 'session-stay-active') {
            e.preventDefault();
            if (countdownInterval) {
                clearInterval(countdownInterval);
                countdownInterval = null;
            }
            const modal = document.getElementById('session-warning-modal');
            if (modal) {
                const Bootstrap = typeof bootstrap !== 'undefined' ? bootstrap : (typeof window.bootstrap !== 'undefined' ? window.bootstrap : null);
                if (Bootstrap) {
                    const bsModal = Bootstrap.Modal.getInstance(modal);
                    if (bsModal) {
                        bsModal.hide();
                    }
                }
            }
            // Resetear el flag de advertencia y reiniciar timer
            warningShown = false;
            resetTimer();
        } else if (e.target && e.target.id === 'session-logout-now') {
            e.preventDefault();
            if (countdownInterval) {
                clearInterval(countdownInterval);
                countdownInterval = null;
            }
            logout();
        }
    });
    
    // Inicializar cuando el DOM esté listo y Bootstrap esté disponible
    function initWhenReady() {
        // Verificar que Bootstrap esté disponible
        const Bootstrap = typeof bootstrap !== 'undefined' ? bootstrap : (typeof window.bootstrap !== 'undefined' ? window.bootstrap : null);
        if (!Bootstrap) {
            // Si Bootstrap no está disponible, esperar un poco más
            setTimeout(initWhenReady, 100);
            return;
        }
        
        // Verificar que el body tenga el atributo
        const body = document.body;
        if (!body) {
            setTimeout(initWhenReady, 100);
            return;
        }
        
        // Inicializar
        initializeTimeout();
    }
    
    // Inicializar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            // Esperar un poco para asegurar que Bootstrap esté cargado
            setTimeout(initWhenReady, 200);
        });
    } else {
        // DOM ya está listo, esperar un poco para Bootstrap
        setTimeout(initWhenReady, 200);
    }
})();
