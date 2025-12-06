// Gestión de medidas predefinidas de tableros
(function() {
    // Medidas predefinidas en centímetros (unidad base)
    const medidasPredefinidas = {
        // Tableros muy comunes en carpintería (Chile / Latam)
        'osb-122x244':      { ancho: 122, alto: 244, nombre: 'OSB' },
        'mdf-122x244':      { ancho: 122, alto: 244, nombre: 'MDF' },
        'mdf-183x244':      { ancho: 183, alto: 244, nombre: 'MDF' },
        'melamina-183x244': { ancho: 183, alto: 244, nombre: 'Melamina' },
        'contrachapado':    { ancho: 122, alto: 244, nombre: 'Contrachapado' },
        'tablero-152x244':  { ancho: 152, alto: 244, nombre: 'Tablero' },
        'custom': { ancho: null, alto: null, nombre: 'Personalizado' }
    };

    // Funciones de conversión
    function convertirDesdeCm(valor, unidad) {
        const conversiones = {
            'cm': 1.0,
            'm': 0.01,
            'in': 1/2.54,
            'ft': 1/30.48,
        };
        return round(valor * (conversiones[unidad] || 1.0), 2);
    }
    
    function round(valor, decimales) {
        return Math.round(valor * Math.pow(10, decimales)) / Math.pow(10, decimales);
    }
    
    function obtenerSimbolo(unidad) {
        const simbolos = {
            'cm': 'cm',
            'm': 'm',
            'in': 'in',
            'ft': 'ft'
        };
        return simbolos[unidad] || 'cm';
    }
    
    function actualizarBotonesMedidas() {
        const unidadSelector = document.getElementById('unidad_medida_selector');
        if (!unidadSelector) return;
        
        const unidad = unidadSelector.value;
        const simbolo = obtenerSimbolo(unidad);
        
        document.querySelectorAll('.medida-btn').forEach(btn => {
            const key = btn.dataset.medida;
            if (key && medidasPredefinidas[key]) {
                const medida = medidasPredefinidas[key];
                const anchoConvertido = convertirDesdeCm(medida.ancho, unidad);
                const altoConvertido = convertirDesdeCm(medida.alto, unidad);
                btn.textContent = `${medida.nombre} (${anchoConvertido}×${altoConvertido}${simbolo})`;
            }
        });
    }

    document.addEventListener('DOMContentLoaded', function() {
        const anchoInput = document.getElementById('ancho_tablero');
        const altoInput = document.getElementById('alto_tablero');
        const unidadSelector = document.getElementById('unidad_medida_selector');
        
        if (!anchoInput || !altoInput) return;

        // Crear contenedor de botones si no existe
        let container = document.getElementById('medidas-pred-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'medidas-pred-container';
            container.className = 'medidas-pred-selector';
            container.innerHTML = '<label class="form-label">📏 Medidas Predefinidas:</label>';
            
            // Insertar antes del selector de unidades
            const unidadField = unidadSelector ? unidadSelector.closest('.row') : null;
            const cardBody = unidadField ? unidadField.closest('.card-body') : document.querySelector('.card-body');
            if (cardBody) {
                const unidadRow = unidadField || cardBody.querySelector('.row');
                if (unidadRow) {
                    cardBody.insertBefore(container, unidadRow);
                } else {
                    cardBody.insertBefore(container, cardBody.firstChild);
                }
            }
        }

        // Crear botones para cada medida
        Object.keys(medidasPredefinidas).forEach(key => {
            if (key === 'custom') return; // Saltar custom
            
            const medida = medidasPredefinidas[key];
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'medida-btn';
            btn.dataset.medida = key;
            btn.dataset.anchoCm = medida.ancho;
            btn.dataset.altoCm = medida.alto;
            
            // Actualizar texto inicial (en cm por defecto)
            const unidad = unidadSelector ? unidadSelector.value : 'cm';
            const simbolo = obtenerSimbolo(unidad);
            const anchoConvertido = convertirDesdeCm(medida.ancho, unidad);
            const altoConvertido = convertirDesdeCm(medida.alto, unidad);
            btn.textContent = `${medida.nombre} (${anchoConvertido}×${altoConvertido}${simbolo})`;
            
            btn.addEventListener('click', function() {
                // Remover clase active de todos los botones
                document.querySelectorAll('.medida-btn').forEach(b => b.classList.remove('active'));
                // Agregar clase active al botón clickeado
                btn.classList.add('active');
                
                // Obtener unidad actual
                const unidadActual = unidadSelector ? unidadSelector.value : 'cm';
                const anchoValor = convertirDesdeCm(medida.ancho, unidadActual);
                const altoValor = convertirDesdeCm(medida.alto, unidadActual);
                
                // Establecer valores en la unidad actual
                anchoInput.value = anchoValor;
                altoInput.value = altoValor;
                
                // Disparar evento change para validación
                anchoInput.dispatchEvent(new Event('change', { bubbles: true }));
                altoInput.dispatchEvent(new Event('change', { bubbles: true }));
            });
            
            container.appendChild(btn);
        });

        // Actualizar botones cuando cambia la unidad
        if (unidadSelector) {
            unidadSelector.addEventListener('change', function() {
                actualizarBotonesMedidas();
                // Limpiar selección de botones cuando cambia la unidad
                document.querySelectorAll('.medida-btn').forEach(b => b.classList.remove('active'));
            });
        }

        // Detectar cuando el usuario cambia manualmente los valores
        anchoInput.addEventListener('input', function() {
            document.querySelectorAll('.medida-btn').forEach(b => b.classList.remove('active'));
        });
        
        altoInput.addEventListener('input', function() {
            document.querySelectorAll('.medida-btn').forEach(b => b.classList.remove('active'));
        });
        
        // Inicializar botones con la unidad actual
        actualizarBotonesMedidas();
    });
})();

