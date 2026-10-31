// Gestión de medidas predefinidas de tableros
(function() {
    // Catálogo renderizado por Django: una sola fuente para HTML y comportamiento.
    const medidasPredefinidas = {};

    // Funciones de conversión
    function convertirDesdeCm(valor, unidad) {
        const conversiones = {
            'cm': 1.0,
            'm': 0.01,
            'mm': 10.0,
            'in': 1/2.54,
            'ft': 1/30.48,
        };
        return round(valor * (conversiones[unidad] || 1.0), 6);
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
        if (dropdownButton && dropdownButton.textContent !== 'Elegir medidas habituales') {
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

        const dropdownButton = document.getElementById('tableros-dropdown');
        if (!anchoInput || !altoInput || !container || !dropdownButton) return;
        if (container.dataset.medidasReady) return;
        container.dataset.medidasReady = 'true';

        container.querySelectorAll('.dropdown-item[data-medida]').forEach(dropdownItem => {
            const key = dropdownItem.dataset.medida;
            const medida = {
                ancho: Number(dropdownItem.dataset.anchoCm),
                alto: Number(dropdownItem.dataset.altoCm),
                nombre: dropdownItem.dataset.nombre,
            };
            medidasPredefinidas[key] = medida;

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
                dropdownButton.textContent = 'Elegir medidas habituales';
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
                dropdownButton.textContent = 'Elegir medidas habituales';
                    dropdownButton.removeAttribute('data-tablero-seleccionado');
                }
            }
        });

        // Inicializar dropdown con la unidad actual
        actualizarDropdownMedidas();
    }

    // Ejecutar cuando el DOM y Bootstrap estén listos
    function iniciar() {
        inicializarDropdown();
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

