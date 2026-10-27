/* Ayuda local; el servidor conserva la validación definitiva de la cuenta. */
(() => {
  'use strict';
  const form = document.querySelector('[data-auth-feedback]');
  if (!form) return;
  const inputs = [...form.querySelectorAll('input:not([type="hidden"])')];
  const summary = form.querySelector('[data-auth-summary]');
  const password = form.elements.namedItem('password1');
  const confirmation = form.elements.namedItem('password2');
  const minimum = Number(form.dataset.minPassword || 0);
  form.classList.add('auth-feedback-ready');

  function localError(input) {
    if (!input.value) return 'Completa este campo para continuar.';
    if (input.type === 'email' && input.validity.typeMismatch) return 'Escribe un correo válido, por ejemplo nombre@correo.cl.';
    if (input.validity.tooLong) return `Usa como máximo ${input.maxLength} caracteres.`;
    if (input === password) {
      if ([...input.value].length < minimum) return `Usa al menos ${minimum} caracteres.`;
      if (form.dataset.rejectsNumeric === 'true' && /^\p{Nd}+$/u.test(input.value)) return 'Añade letras o símbolos: la contraseña no puede contener solo números.';
    }
    if (input === confirmation && password.value !== confirmation.value) return 'Las contraseñas no coinciden. Repite la misma contraseña.';
    return '';
  }
  function check(input) {
    const wrapper = input.closest('[data-auth-field]');
    const errors = wrapper.querySelector('[data-field-errors]');
    const message = localError(input);
    if (errors.dataset.message !== message) {
      errors.replaceChildren();
      if (message) {
        const line = document.createElement('p'), icon = document.createElement('span');
        icon.textContent = '!'; icon.setAttribute('aria-hidden', 'true');
        line.append(icon, ` ${message}`); errors.append(line);
      }
      errors.dataset.message = message;
    }
    errors.hidden = !message;
    input.setAttribute('aria-invalid', String(Boolean(message)));
    wrapper.dataset.touched = 'true';
    return !message;
  }
  function guide() {
    if (!password) return;
    for (const item of form.querySelectorAll('[data-password-rule]')) {
      const satisfied = Boolean(password.value) && (item.dataset.passwordRule === 'length' ? [...password.value].length >= minimum : !/^\p{Nd}+$/u.test(password.value));
      item.dataset.satisfied = String(satisfied);
      item.querySelector('[data-rule-icon]').textContent = satisfied ? '✓' : '○';
    }
    const match = form.querySelector('[data-password-match]');
    const touched = confirmation.closest('[data-auth-field]').dataset.touched;
    match.hidden = !(touched && confirmation.value && password.value === confirmation.value);
    const message = match.hidden ? '' : '✓ Las contraseñas coinciden.';
    if (match.textContent !== message) match.textContent = message;
  }
  for (const input of inputs) {
    if (input.getAttribute('aria-invalid') === 'true') input.closest('[data-auth-field]').dataset.touched = 'true';
    input.addEventListener('blur', () => { check(input); guide(); });
    input.addEventListener('input', () => {
      if (input.closest('[data-auth-field]').dataset.touched) check(input);
      if (input === password && confirmation.closest('[data-auth-field]').dataset.touched) check(confirmation);
      guide();
    });
  }
  form.addEventListener('submit', event => {
    const valid = inputs.map(check).every(Boolean);
    guide();
    if (!valid) {
      event.preventDefault(); summary.textContent = 'Revisa los campos señalados para continuar.';
      summary.hidden = false; summary.focus();
    }
  });
  guide();
  if (!summary.hidden) summary.focus();
})();
