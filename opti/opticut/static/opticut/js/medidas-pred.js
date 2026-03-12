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
            'mm': 10.0,
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
            'mm': 'mm',
            'in': 'in',
            'ft': 'ft'
        };
        return simbolos[unidad] || 'cm';
    }
    
    function actualizarDropdownMedidas() {
        const unidadSelector = document.getElementById('unidad_medida_selector');
        if (!unidadSelector) return;
        
        const unidad = unidadSelector.value;
        const simbolo = obtenerSimbolo(unidad);
        const dropdownButton = document.getElementById('tableros-dropdown');
        
        // Actualizar todas las opciones del dropdown
        document.querySelectorAll('.dropdown-item[data-medida]').forEach(item => {
            const key = item.dataset.medida;
            if (key && medidasPredefinidas[key]) {
                const medida = medidasPredefinidas[key];
                const anchoConvertido = convertirDesdeCm(medida.ancho, unidad);
                const altoConvertido = convertirDesdeCm(medida.alto, unidad);
                item.textContent = `${medida.nombre} (${anchoConvertido}×${altoConvertido} ${simbolo})`;
            }
        });
        
        // Si hay un tablero seleccionado, actualizar el texto del botón también
        if (dropdownButton && dropdownButton.textContent !== 'Seleccionar tablero predefinido...') {
            const selectedItem = document.querySelector('.dropdown-item.active') || 
                                Array.from(document.querySelectorAll('.dropdown-item[data-medida]')).find(item => {
                                    const anchoInput = document.getElementById('ancho_tablero');
                                    const altoInput = document.getElementById('alto_tablero');
                                    if (!anchoInput || !altoInput) return false;
                                    
                                    const unidadActual = unidadSelector.value;
                                    const anchoValor = parseFloat(anchoInput.value);
                                    const altoValor = parseFloat(altoInput.value);
                                    const anchoCm = parseFloat(item.dataset.anchoCm);
                                    const altoCm = parseFloat(item.dataset.altoCm);
                                    
                                    const anchoConvertido = convertirDesdeCm(anchoCm, unidadActual);
                                    const altoConvertido = convertirDesdeCm(altoCm, unidadActual);
                                    
                                    return Math.abs(anchoValor - anchoConvertido) < 0.01 && 
                                           Math.abs(altoValor - altoConvertido) < 0.01;
                                });
            
            if (selectedItem) {
                // Obtener el nombre y dimensiones del tablero seleccionado
                const key = selectedItem.dataset.medida;
                if (key && medidasPredefinidas[key]) {
                    const medida = medidasPredefinidas[key];
                    const anchoConvertido = convertirDesdeCm(medida.ancho, unidad);
                    const altoConvertido = convertirDesdeCm(medida.alto, unidad);
                    dropdownButton.textContent = `${medida.nombre} (${anchoConvertido}×${altoConvertido} ${simbolo})`;
                } else {
                dropdownButton.textContent = selectedItem.textContent;
                }
            }
        }
    }

    // Esperar a que el DOM y Bootstrap estén listos
    function inicializarDropdown() {
        const anchoInput = document.getElementById('ancho_tablero');
        const altoInput = document.getElementById('alto_tablero');
        const unidadSelector = document.getElementById('unidad_medida_selector');
        const container = document.getElementById('medidas-pred-container');
        
        // Verificar que todos los elementos necesarios existan
        if (!anchoInput || !altoInput || !container) {
            console.log('Esperando elementos del DOM...', {
                anchoInput: !!anchoInput,
                altoInput: !!altoInput,
                container: !!container
            });
            // Reintentar después de un breve delay si los elementos no están listos
            setTimeout(inicializarDropdown, 100);
            return;
        }
        
        console.log('Inicializando dropdown de tableros predefinidos...');
        
        // Limpiar completamente el contenedor para eliminar cualquier código antiguo (botones)
        container.innerHTML = '';
        
        // Crear estructura del dropdown
        // Crear label
        const label = document.createElement('label');
        label.className = 'form-label mb-2';
        label.textContent = 'Tableros Predefinidos:';
        label.setAttribute('for', 'tableros-dropdown');
        container.appendChild(label);
        
        // Crear dropdown wrapper
        const dropdownWrapper = document.createElement('div');
        dropdownWrapper.className = 'dropdown mb-3';
        
        const dropdownButton = document.createElement('button');
        dropdownButton.className = 'btn btn-outline-secondary dropdown-toggle w-100';
        dropdownButton.type = 'button';
        dropdownButton.id = 'tableros-dropdown';
        dropdownButton.setAttribute('data-bs-toggle', 'dropdown');
        dropdownButton.setAttribute('data-bs-auto-close', 'true');
        dropdownButton.setAttribute('aria-expanded', 'false');
        dropdownButton.textContent = 'Seleccionar tablero predefinido...';
        
        const dropdownMenu = document.createElement('ul');
        dropdownMenu.className = 'dropdown-menu w-100';
        dropdownMenu.setAttribute('aria-labelledby', 'tableros-dropdown');
        
        dropdownWrapper.appendChild(dropdownButton);
        dropdownWrapper.appendChild(dropdownMenu);
        container.appendChild(dropdownWrapper);
        
        // Inicializar Bootstrap Dropdown
        setTimeout(function() {
            if (typeof bootstrap !== 'undefined' && bootstrap.Dropdown) {
                new bootstrap.Dropdown(dropdownButton);
            } else if (typeof window.bootstrap !== 'undefined' && window.bootstrap.Dropdown) {
                new window.bootstrap.Dropdown(dropdownButton);
            }
        }, 100);

        // Crear opciones del dropdown para cada medida
        Object.keys(medidasPredefinidas).forEach(key => {
            if (key === 'custom') return; // Saltar custom
            
            const medida = medidasPredefinidas[key];
            const listItem = document.createElement('li');
            
            const dropdownItem = document.createElement('a');
            dropdownItem.className = 'dropdown-item';
            dropdownItem.href = '#';
            dropdownItem.dataset.medida = key;
            dropdownItem.dataset.anchoCm = medida.ancho;
            dropdownItem.dataset.altoCm = medida.alto;
            
            // Actualizar texto inicial (en cm por defecto)
            const unidad = unidadSelector ? unidadSelector.value : 'cm';
            const simbolo = obtenerSimbolo(unidad);
            const anchoConvertido = convertirDesdeCm(medida.ancho, unidad);
            const altoConvertido = convertirDesdeCm(medida.alto, unidad);
            dropdownItem.textContent = `${medida.nombre} (${anchoConvertido}×${altoConvertido} ${simbolo})`;
            
            dropdownItem.addEventListener('click', function(e) {
                e.preventDefault();
                
                // Obtener unidad actual
                const unidadActual = unidadSelector ? unidadSelector.value : 'cm';
                const anchoValor = convertirDesdeCm(medida.ancho, unidadActual);
                const altoValor = convertirDesdeCm(medida.alto, unidadActual);
                const simbolo = obtenerSimbolo(unidadActual);
                
                // Marcar que el cambio viene del dropdown
                window.cambioDesdeDropdown = true;
                
                // Establecer valores en la unidad actual
                anchoInput.value = anchoValor;
                altoInput.value = altoValor;
                
                // Actualizar texto del botón dropdown con nombre y dimensiones
                const textoBoton = `${medida.nombre} (${anchoValor}×${altoValor} ${simbolo})`;
                dropdownButton.textContent = textoBoton;
                dropdownButton.setAttribute('data-tablero-seleccionado', key);
                
                // Cerrar el dropdown de Bootstrap si está abierto
                if (typeof bootstrap !== 'undefined' && bootstrap.Dropdown) {
                    const dropdownInstance = bootstrap.Dropdown.getInstance(dropdownButton);
                    if (dropdownInstance) {
                        dropdownInstance.hide();
                    }
                }
                
                // Disparar evento change para validación (después de un pequeño delay para que se procese el cambio)
                setTimeout(function() {
                anchoInput.dispatchEvent(new Event('change', { bubbles: true }));
                altoInput.dispatchEvent(new Event('change', { bubbles: true }));
                    window.cambioDesdeDropdown = false;
                }, 50);
                
                // Buscar y seleccionar automáticamente el material correspondiente
                buscarYSeleccionarMaterial(medida.nombre, medida.ancho, medida.alto);
            });
            
            listItem.appendChild(dropdownItem);
            dropdownMenu.appendChild(listItem);
        });

        // Actualizar dropdown cuando cambia la unidad
        if (unidadSelector) {
            unidadSelector.addEventListener('change', function() {
                actualizarDropdownMedidas();
            });
        }

        // Detectar cuando el usuario cambia manualmente los valores
        anchoInput.addEventListener('input', function() {
            // Si el cambio viene del dropdown, no hacer nada
            if (window.cambioDesdeDropdown) {
                return;
            }
            
            const dropdownButton = document.getElementById('tableros-dropdown');
            if (dropdownButton) {
                // Verificar si los valores coinciden con algún tablero predefinido
                const unidadActual = unidadSelector ? unidadSelector.value : 'cm';
                const anchoValor = parseFloat(anchoInput.value);
                const altoValor = parseFloat(altoInput.value);
                const simbolo = obtenerSimbolo(unidadActual);
                
                let encontrado = false;
                for (const key in medidasPredefinidas) {
                    if (key === 'custom') continue;
                    const medida = medidasPredefinidas[key];
                    const anchoConvertido = convertirDesdeCm(medida.ancho, unidadActual);
                    const altoConvertido = convertirDesdeCm(medida.alto, unidadActual);
                    
                    if (Math.abs(anchoValor - anchoConvertido) < 0.01 && 
                        Math.abs(altoValor - altoConvertido) < 0.01) {
                        dropdownButton.textContent = `${medida.nombre} (${anchoConvertido}×${altoConvertido} ${simbolo})`;
                        dropdownButton.setAttribute('data-tablero-seleccionado', key);
                        encontrado = true;
                        break;
                    }
                }
                
                if (!encontrado) {
                dropdownButton.textContent = 'Seleccionar tablero predefinido...';
                    dropdownButton.removeAttribute('data-tablero-seleccionado');
                }
            }
        });
        
        altoInput.addEventListener('input', function() {
            // Si el cambio viene del dropdown, no hacer nada
            if (window.cambioDesdeDropdown) {
                return;
            }
            
            const dropdownButton = document.getElementById('tableros-dropdown');
            if (dropdownButton) {
                // Verificar si los valores coinciden con algún tablero predefinido
                const unidadActual = unidadSelector ? unidadSelector.value : 'cm';
                const anchoValor = parseFloat(anchoInput.value);
                const altoValor = parseFloat(altoInput.value);
                const simbolo = obtenerSimbolo(unidadActual);
                
                let encontrado = false;
                for (const key in medidasPredefinidas) {
                    if (key === 'custom') continue;
                    const medida = medidasPredefinidas[key];
                    const anchoConvertido = convertirDesdeCm(medida.ancho, unidadActual);
                    const altoConvertido = convertirDesdeCm(medida.alto, unidadActual);
                    
                    if (Math.abs(anchoValor - anchoConvertido) < 0.01 && 
                        Math.abs(altoValor - altoConvertido) < 0.01) {
                        dropdownButton.textContent = `${medida.nombre} (${anchoConvertido}×${altoConvertido} ${simbolo})`;
                        dropdownButton.setAttribute('data-tablero-seleccionado', key);
                        encontrado = true;
                        break;
                    }
                }
                
                if (!encontrado) {
                dropdownButton.textContent = 'Seleccionar tablero predefinido...';
                    dropdownButton.removeAttribute('data-tablero-seleccionado');
                }
            }
        });
        
        // Inicializar dropdown con la unidad actual
        actualizarDropdownMedidas();
    }
    
    // Ejecutar cuando el DOM y Bootstrap estén listos
    function iniciar() {
        // Verificar si Bootstrap está disponible
        if (typeof bootstrap === 'undefined' && typeof window.bootstrap === 'undefined') {
            // Esperar a que Bootstrap se cargue
            setTimeout(iniciar, 100);
            return;
        }
        
        // Verificar si el DOM está listo
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', function() {
                setTimeout(inicializarDropdown, 50);
            });
        } else {
            // DOM ya está listo, ejecutar después de un pequeño delay
            setTimeout(inicializarDropdown, 50);
        }
    }
    
    // Función para buscar y seleccionar material correspondiente
    function buscarYSeleccionarMaterial(nombreMaterial, anchoCm, altoCm) {
        // Intentar múltiples veces para asegurar que los datos estén disponibles
        function intentarBuscar(intentos) {
            if (intentos <= 0) return;
            
            const materialSelect = document.getElementById('material_select');
            if (!materialSelect) {
                setTimeout(function() { intentarBuscar(intentos - 1); }, 100);
                return;
            }
            
            // Verificar que los datos de materiales estén disponibles
            if (!window.materialData) {
                setTimeout(function() { intentarBuscar(intentos - 1); }, 100);
                return;
            }
            
            // Buscar en las opciones del selector
            const opciones = materialSelect.options;
            let materialEncontrado = null;
            
            // Buscar material que coincida por nombre y dimensiones (con tolerancia de 0.1 cm)
            for (let i = 0; i < opciones.length; i++) {
                const option = opciones[i];
                const materialId = option.value;
                
                if (!materialId) continue; // Saltar opción vacía
                
                // Obtener datos del material desde el contexto global
                if (window.materialData[materialId]) {
                    const material = window.materialData[materialId];
                    
                    // Comparar nombre (case insensitive) y dimensiones (con tolerancia)
                    const nombreCoincide = material.nombre && 
                        material.nombre.toLowerCase().includes(nombreMaterial.toLowerCase());
                    const anchoCoincide = material.ancho && 
                        Math.abs(material.ancho - anchoCm) < 0.1;
                    const altoCoincide = material.alto && 
                        Math.abs(material.alto - altoCm) < 0.1;
                    
                    if (nombreCoincide && anchoCoincide && altoCoincide) {
                        materialEncontrado = materialId;
                        break;
                    }
                }
            }
            
            // Si se encontró un material, seleccionarlo
            if (materialEncontrado) {
                materialSelect.value = materialEncontrado;
                
                // Actualizar precio directamente desde los datos del material
                if (window.materialData && window.materialData[materialEncontrado] && window.materialData[materialEncontrado].precio) {
                    const precioTableroInput = document.getElementById('precio_tablero');
                    if (precioTableroInput) {
                        precioTableroInput.value = window.materialData[materialEncontrado].precio;
                    }
                }
                
                // Disparar evento change para que se ejecuten otros listeners
                const changeEvent = new Event('change', { bubbles: true });
                materialSelect.dispatchEvent(changeEvent);
            }
        }
        
        // Intentar buscar hasta 10 veces (1 segundo máximo)
        intentarBuscar(10);
    }
    
    // Hacer función disponible globalmente
    window.buscarYSeleccionarMaterial = buscarYSeleccionarMaterial;
    
    // Iniciar cuando el script se carga
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', iniciar);
    } else {
        iniciar();
    }
})();

