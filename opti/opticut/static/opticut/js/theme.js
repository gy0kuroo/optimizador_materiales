// Gestión del modo oscuro/claro
(function() {
    // Función para establecer el tema
    function setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
    }

    // Función para obtener el tema preferido
    function getTheme() {
        // Primero verificar si hay un tema guardado en localStorage (preferencia del usuario)
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme) {
            return savedTheme;
        }
        
        // Si no hay tema guardado, verificar si hay un tema preferido del perfil
        // (esto se establece cuando el usuario guarda su perfil)
        const body = document.body;
        const perfilTheme = body.getAttribute('data-perfil-theme');
        if (perfilTheme && perfilTheme !== 'auto') {
            return perfilTheme;
        }
        
        // Si el tema del perfil es 'auto' o no existe, detectar preferencia del sistema
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return 'dark';
        }
        return 'light';
    }

    // Inicializar tema al cargar la página
    document.addEventListener('DOMContentLoaded', function() {
        const theme = getTheme();
        setTheme(theme);
        
        // Actualizar el botón de toggle si existe
        const toggleBtn = document.getElementById('theme-toggle');
        if (toggleBtn) {
            toggleBtn.textContent = theme === 'dark' ? '☀️' : '🌙';
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



