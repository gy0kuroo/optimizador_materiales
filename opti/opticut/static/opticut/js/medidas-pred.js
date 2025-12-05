// Gestión de medidas predefinidas de tableros
(function() {
    const medidasPredefinidas = {
        // Tableros muy comunes en carpintería (Chile / Latam)
        'osb-122x244':      { ancho: 122, alto: 244, nombre: 'OSB ' },
        'mdf-122x244':      { ancho: 122, alto: 244, nombre: 'MDF ' },
        'mdf-183x244':      { ancho: 183, alto: 244, nombre: 'MDF ' },
        'melamina-183x244': { ancho: 183, alto: 244, nombre: 'Melamina ' },
        'contrachapado':    { ancho: 122, alto: 244, nombre: 'Contrachapado ' },
        'tablero-152x244':  { ancho: 152, alto: 244, nombre: 'Tablero ' },
        'custom': { ancho: null, alto: null, nombre: 'Personalizado' }
    };

    document.addEventListener('DOMContentLoaded', function() {
        const anchoInput = document.getElementById('id_ancho');
        const altoInput = document.getElementById('id_alto');
        
        if (!anchoInput || !altoInput) return;

        // Crear contenedor de botones si no existe
        let container = document.getElementById('medidas-pred-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'medidas-pred-container';
            container.className = 'medidas-pred-selector';
            container.innerHTML = '<label class="form-label">📏 Medidas Predefinidas:</label>';
            
        // Insertar antes del campo de ancho
        const anchoField = anchoInput.closest('.col-md-6') || anchoInput.parentElement;
        const cardBody = anchoField.closest('.card-body') || anchoField.closest('.row').parentElement;
        if (cardBody) {
            cardBody.insertBefore(container, cardBody.firstChild);
        } else {
            anchoField.parentElement.insertBefore(container, anchoField.parentElement.firstChild);
        }
        }

        // Crear botones para cada medida
        Object.keys(medidasPredefinidas).forEach(key => {
            if (key === 'custom') return; // Saltar custom
            
            const medida = medidasPredefinidas[key];
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'medida-btn';
            btn.textContent = `${medida.nombre} (${medida.ancho}×${medida.alto}cm)`;
            btn.dataset.medida = key;
            
            btn.addEventListener('click', function() {
                // Remover clase active de todos los botones
                document.querySelectorAll('.medida-btn').forEach(b => b.classList.remove('active'));
                // Agregar clase active al botón clickeado
                btn.classList.add('active');
                
                // Establecer valores
                anchoInput.value = medida.ancho;
                altoInput.value = medida.alto;
                
                // Disparar evento change para validación
                anchoInput.dispatchEvent(new Event('change', { bubbles: true }));
                altoInput.dispatchEvent(new Event('change', { bubbles: true }));
            });
            
            container.appendChild(btn);
        });

        // Detectar cuando el usuario cambia manualmente los valores
        anchoInput.addEventListener('input', function() {
            document.querySelectorAll('.medida-btn').forEach(b => b.classList.remove('active'));
        });
        
        altoInput.addEventListener('input', function() {
            document.querySelectorAll('.medida-btn').forEach(b => b.classList.remove('active'));
        });
    });
})();

