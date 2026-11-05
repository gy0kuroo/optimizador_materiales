(() => {
  'use strict';

  let generatedId = 0;

  function addVisibilityControl(input) {
    if (input.dataset.passwordVisibilityReady === 'true') return;
    const existingButton = input.closest('.password-visibility-field')?.querySelector(':scope > .password-visibility-toggle');
    if (existingButton) {
      existingButton.addEventListener('click', () => {
        const visible = input.type === 'password';
        input.type = visible ? 'text' : 'password';
        const label = visible ? existingButton.dataset.hideLabel : existingButton.dataset.showLabel;
        existingButton.setAttribute('aria-label', label);
        existingButton.setAttribute('aria-pressed', String(visible));
        existingButton.title = label;
      });
      input.dataset.passwordVisibilityReady = 'true';
      return;
    }

    if (!input.id) {
      do {
        generatedId += 1;
        input.id = `password-field-${generatedId}`;
      } while (document.getElementById(input.id) !== input);
    }

    const wrapper = document.createElement('span');
    wrapper.className = 'password-visibility-field';
    input.before(wrapper);
    wrapper.append(input);

    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'btn btn-icon btn-text password-visibility-toggle';
    button.dataset.action = 'text';
    button.dataset.icon = 'eye';
    button.setAttribute('aria-label', 'Mostrar contrase\u00f1a');
    button.setAttribute('aria-controls', input.id);
    button.setAttribute('aria-pressed', 'false');
    button.title = 'Mostrar contrase\u00f1a';

    button.addEventListener('click', () => {
      const visible = input.type === 'password';
      input.type = visible ? 'text' : 'password';
      const label = visible ? 'Ocultar contrase\u00f1a' : 'Mostrar contrase\u00f1a';
      button.setAttribute('aria-label', label);
      button.setAttribute('aria-pressed', String(visible));
      button.title = label;
    });

    wrapper.append(button);
    input.dataset.passwordVisibilityReady = 'true';
  }

  function initialize() {
    document.querySelectorAll('input[type="password"]').forEach(addVisibilityControl);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initialize, {once: true});
  } else {
    initialize();
  }
})();