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

    // Inicializar tema al cargar la página
    document.addEventListener('DOMContentLoaded', function() {
        const theme = getTheme();
        setTheme(theme);

        const fontSize = getFontSize();
        setFontSize(fontSize);

        // Actualizar el botón de toggle si existe
        const toggleBtn = document.getElementById('theme-toggle');
        if (toggleBtn) {
            toggleBtn.textContent = theme === 'dark' ? '☀️' : '🌙';
        }

        // Detectar dropdown tamaño de la preferencia de perfil y actualizar en realtime
        const fontSizeSelect = document.querySelector('select[name="tamanio_fuente"]');
        if (fontSizeSelect) {
            fontSizeSelect.value = fontSize;
            fontSizeSelect.addEventListener('change', function() {
                setFontSize(this.value);
            });
        }

        // Detectar dropdown tema preferido y actualizar en realtime
        const themeSelect = document.querySelector('select[name="tema_preferido"]');
        if (themeSelect) {
            const currentThemeSelection = localStorage.getItem('theme') || document.body.getAttribute('data-perfil-theme') || 'auto';
            themeSelect.value = currentThemeSelection;
            themeSelect.addEventListener('change', function() {
                setTheme(this.value);
            });
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



