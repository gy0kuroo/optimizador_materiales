document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('setup-form');
    if (!form) return;
    const sections = Array.from(form.querySelectorAll('[data-step]'));
    const previous = document.getElementById('setup-prev');
    const next = document.getElementById('setup-next');
    const save = document.getElementById('setup-save');
    const tools = Array.from(form.querySelectorAll('#optional-tools input[type="checkbox"]'));
    const choice = name => form.querySelector(`input[name="${name}"]:checked`)?.value;
    const systemTheme = window.matchMedia('(prefers-color-scheme: dark)');
    let step = 0;

    function renderStep(focus = false) {
        sections.forEach((section, index) => { section.hidden = index !== step; });
        document.querySelectorAll('[data-progress]').forEach((item, index) => {
            if (index === step) item.setAttribute('aria-current', 'step');
            else item.removeAttribute('aria-current');
        });
        previous.hidden = step === 0;
        next.hidden = step === sections.length - 1;
        save.hidden = step !== sections.length - 1;
        document.getElementById('setup-step-text').textContent = `Paso ${step + 1} de 2 · Puedes cambiar estas preferencias después.`;
        if (focus) sections[step].querySelector('h2').focus();
    }

    function preview() {
        const custom = choice('modo') === 'personalizado';
        document.getElementById('optional-tools').hidden = !custom;
        const selected = custom ? tools.filter(input => input.checked) : [];
        document.getElementById('tools-count').textContent = `${selected.length} seleccionadas`;
        tools.forEach(input => {
            const state = input.closest('label')?.querySelector('.setup-tool-state');
            if (state) state.textContent = input.checked ? 'Seleccionada' : 'Seleccionar';
        });
        const theme = choice('tema_preferido') || 'auto';
        document.documentElement.dataset.theme = theme === 'auto' ? (systemTheme.matches ? 'dark' : 'light') : theme;
        const sizes = {small: '15px', normal: '16px', large: '18px', xlarge: '20px'};
        document.documentElement.style.fontSize = sizes[choice('tamanio_fuente')] || sizes.normal;
        document.getElementById('setup-summary').textContent = selected.length
            ? `Tu menú incluirá Optimización, Historial y ${selected.length} herramientas adicionales.`
            : 'Tu menú incluirá Optimización e Historial. Las demás herramientas podrán activarse más adelante.';
    }

    previous.addEventListener('click', () => { step = Math.max(0, step - 1); renderStep(true); });
    next.addEventListener('click', () => { step = Math.min(sections.length - 1, step + 1); renderStep(true); });
    form.addEventListener('change', preview);
    // Enter en el primer paso avanza; nunca guarda antes de revisar la apariencia.
    form.addEventListener('submit', event => {
        if (step === 0) { event.preventDefault(); step = 1; renderStep(true); }
    });
    systemTheme.addEventListener('change', preview);
    renderStep();
    preview();
});
