// Gestiona los cambios de tema y preferencias después del primer pintado.
(() => {
    const root = document.documentElement;
    const systemTheme = window.matchMedia?.('(prefers-color-scheme: dark)');
    const sessionKey = root.getAttribute('data-theme-session-key');
    const toggle = document.getElementById('theme-toggle');

    function readLocal(key) {
        try { return localStorage.getItem(key); } catch (_) { return null; }
    }

    function writeLocal(key, value) {
        try { localStorage.setItem(key, value); } catch (_) { /* Preferencia en esta página. */ }
    }

    function updateToggle() {
        if (!toggle) return;
        const dark = root.getAttribute('data-theme') === 'dark';
        toggle.setAttribute('data-icon', dark ? 'sun' : 'moon');
        const label = dark ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro';
        toggle.setAttribute('aria-label', label);
        toggle.title = label;
    }

    function setTheme(choice) {
        const resolved = choice === 'auto' ? (systemTheme?.matches ? 'dark' : 'light') : choice;
        root.setAttribute('data-theme', resolved);
        root.setAttribute('data-theme-choice', choice);
        updateToggle();
    }

    function toggleTheme() {
        const next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
        if (sessionKey) {
            try {
                sessionStorage.setItem(sessionKey, `${root.getAttribute('data-theme-profile')}:${next}`);
            } catch (_) { /* El cambio sigue funcionando en esta página. */ }
        }
        setTheme(next);
    }

    function clearTemporaryTheme() {
        if (!sessionKey) return;
        try { sessionStorage.removeItem(sessionKey); } catch (_) { /* Sin almacenamiento. */ }
    }

    function setFontSize(fontSize) {
        const sizes = {small: '15px', normal: '16px', large: '18px', xlarge: '20px'};
        fontSize = Object.hasOwn(sizes, fontSize) ? fontSize : 'normal';
        root.style.fontSize = sizes[fontSize];
        document.body.setAttribute('data-font-size', fontSize);
        writeLocal('fontSize', fontSize);
    }

    document.addEventListener('DOMContentLoaded', () => {
        const savedTheme = root.getAttribute('data-theme-profile') || root.getAttribute('data-theme-choice');
        writeLocal('theme', savedTheme);
        // El formulario conserva el valor del perfil o del POST cuando Django devuelve errores.
        const themeSelect = document.querySelector('[data-pref-key="tema_preferido"]');
        themeSelect?.addEventListener('change', () => {
            clearTemporaryTheme();
            setTheme(themeSelect.value);
        });
        themeSelect?.form?.addEventListener('formdata', clearTemporaryTheme);

        const fontSize = document.body.getAttribute('data-font-size') || readLocal('fontSize') || 'normal';
        setFontSize(fontSize);
        const fontSizeSelect = document.querySelector('select[name="tamanio_fuente"]');

        document.querySelectorAll('[data-pref-key]').forEach(input => {
            const key = input.getAttribute('data-pref-key');
            if (key === 'tema_preferido') return;
            const saved = readLocal(key) || document.body.getAttribute(`data-perfil-${key}`);
            if (saved) input.value = saved;
            input.addEventListener('change', () => {
                writeLocal(key, input.value);
                document.body.setAttribute(`data-pref-${key}`, input.value);
                if (key === 'tamanio_fuente') setFontSize(input.value);
            });
        });
        if (fontSizeSelect && !fontSizeSelect.value) fontSizeSelect.value = fontSize;

        if (toggle) {
            updateToggle();
            toggle.addEventListener('click', toggleTheme);
            toggle.hidden = false;
        }
    });

    systemTheme?.addEventListener('change', () => {
        if (root.getAttribute('data-theme-choice') === 'auto') setTheme('auto');
    });
    window.addEventListener('pageshow', updateToggle);
})();
