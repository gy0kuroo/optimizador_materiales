// Gestión del modo oscuro/claro
(function() {
    // Función para detectar el tema del sistema
    function getSystemTheme() {
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return 'dark';
        }
        return 'light';
    }

    // Función para resolver tema con 'auto'
    function resolveTheme(theme) {
        if (!theme || theme === 'auto') {
            return getSystemTheme();
        }
        return theme === 'dark' ? 'dark' : 'light';
    }

    // Función para establecer el tema (almacena la elección original)
    function setTheme(theme) {
        const resolved = resolveTheme(theme);
        document.documentElement.setAttribute('data-theme', resolved);
        document.documentElement.setAttribute('data-theme-choice', theme);

        localStorage.setItem('theme', theme);
        localStorage.setItem('tema_preferido', theme);

        const toggleBtn = document.getElementById('theme-toggle');
        if (toggleBtn) {
            toggleBtn.textContent = resolved === 'dark' ? '☀️' : '🌙';
        }

        const themeSelect = document.querySelector('select[name="tema_preferido"]');
        if (themeSelect) {
            themeSelect.value = theme;
        }
    }

    // Función para obtener el tema preferido (prioridad localStorage > perfil > system)
    function getTheme() {
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme) {
            return savedTheme;
        }

        const body = document.body;
        const perfilTheme = body.getAttribute('data-perfil-theme');
        if (perfilTheme) {
            return perfilTheme;
        }

        return 'auto';
    }

    // Función genérica para preferencias
    function setPreference(key, value) {
        if (!key) {
            return;
        }

        localStorage.setItem(key, value);
        document.body.setAttribute('data-pref-' + key, value);

        if (key === 'tema_preferido') {
            setTheme(value);
        } else if (key === 'tamanio_fuente') {
            setFontSize(value);
        }
    }

    function getPreference(key, fallback) {
        const saved = localStorage.getItem(key);
        if (saved != null && saved !== '') {
            return saved;
        }

        const body = document.body;
        if (body) {
            const dataValue = body.getAttribute('data-perfil-' + key);
            if (dataValue != null && dataValue !== '') {
                return dataValue;
            }
        }

        return fallback;
    }

    // Función para establecer tamaño de fuentes
    function setFontSize(fontSize) {
        document.body.setAttribute('data-font-size', fontSize);
        localStorage.setItem('fontSize', fontSize);
    }

    // Obtener tamaño de fuente
    function getFontSize() {
        const savedFontSize = localStorage.getItem('fontSize');
        if (savedFontSize) {
            return savedFontSize;
        }

        const body = document.body;
        const perfilFontSize = body.getAttribute('data-font-size');

        if (perfilFontSize) {
            return perfilFontSize;
        }

        return 'normal';
    }

    // Inicializar preferencias al cargar la página
    document.addEventListener('DOMContentLoaded', function() {
        // Tema y fontSize (comportamiento base existente)
        const theme = getTheme();
        setTheme(theme);

        const fontSize = getFontSize();
        setFontSize(fontSize);

        // Botón toggle de tema
        const toggleBtn = document.getElementById('theme-toggle');
        if (toggleBtn) {
            const currentResolvedTheme = resolveTheme(theme);
            toggleBtn.textContent = currentResolvedTheme === 'dark' ? '☀️' : '🌙';
            toggleBtn.addEventListener('click', function() {
                const nextTheme = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
                setPreference('tema_preferido', nextTheme);
            });
        }

        // Sincronizar cambios automáticos para controles en la página marcados con data-pref-key
        const prefInputs = document.querySelectorAll('[data-pref-key]');

        prefInputs.forEach(function(input) {
            const prefKey = input.getAttribute('data-pref-key');
            const prefsValue = getPreference(prefKey, '');

            if (prefsValue !== null && prefsValue !== '') {
                input.value = prefsValue;
            }

            input.addEventListener('change', function() {
                setPreference(prefKey, this.value);

                // Si el cambio es de tema o font, aplicar al inmediato
                if (prefKey === 'tema_preferido') {
                    setTheme(this.value);
                } else if (prefKey === 'tamanio_fuente') {
                    setFontSize(this.value);
                }
            });
        });

        // Asegurar que el select de tema también refleje la preferencia
        const themeSelect = document.querySelector('select[name="tema_preferido"]');
        if (themeSelect) {
            themeSelect.value = getPreference('tema_preferido', theme);
        }

        // Asegurar que el select de tamaño de fuente refleje la preferencia
        const fontSizeSelect = document.querySelector('select[name="tamanio_fuente"]');
        if (fontSizeSelect) {
            fontSizeSelect.value = getPreference('tamanio_fuente', fontSize);
        }
    });

    // Función para alternar tema
    window.toggleTheme = function() {
        const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        setTheme(newTheme);
        
        const toggleBtn = document.getElementById('theme-toggle');
        if (toggleBtn) {
            toggleBtn.textContent = newTheme === 'dark' ? '☀️' : '🌙';
        }
    };

    // Escuchar cambios en la preferencia del sistema
    if (window.matchMedia) {
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(e) {
            if (!localStorage.getItem('theme')) {
                setTheme(e.matches ? 'dark' : 'light');
            }
        });
    }
})();



