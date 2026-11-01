/* Mantiene la relación entre etiquetas y campos al añadir o quitar piezas. */
(() => {
  'use strict';
  function reindex(container) {
    const rows = [...container.querySelectorAll('.pieza-form')];
    rows.forEach((row, index) => {
      for (const element of row.querySelectorAll('[name],[id],[for],[aria-describedby],[aria-labelledby]')) {
        for (const attribute of ['name', 'id', 'for', 'aria-describedby', 'aria-labelledby']) {
          const value = element.getAttribute(attribute);
          if (value) element.setAttribute(attribute, value.replace(/form-\d+-/g, `form-${index}-`));
        }
      }
    });
    return rows.length;
  }
  const initialized = new WeakSet();
  function init(container, addButton, totalFormsInput) {
    if (!container || !addButton || !totalFormsInput || initialized.has(container)) return;
    initialized.add(container);
    const rows = () => [...container.querySelectorAll('.pieza-form')];
    function sync() {
      const count = reindex(container);
      totalFormsInput.value = count;
      container.querySelectorAll('.pieza-numero').forEach((label, index) => {
        label.textContent = index + 1;
      });
      container.querySelectorAll('.remove-pieza').forEach(button => {
        button.classList.toggle('remove-pieza-hidden', count <= 1);
      });
    }
    addButton.addEventListener('click', async () => {
      if (rows().length >= 20) {
        const message = 'Puedes añadir hasta 20 tipos de pieza.';
        if (window.cutlessAlerta) await window.cutlessAlerta({titulo:'Límite de tipos de pieza', mensaje:message});
        else window.alert(message);
        return;
      }
      const source = rows()[0];
      if (!source) return;
      const copy = source.cloneNode(true);
      copy.querySelectorAll('.text-danger, .alert-danger').forEach(error => error.remove());
      copy.querySelectorAll('input, select, textarea').forEach(input => {
        if (input.type !== 'hidden') input.value = input.name.includes('cantidad') ? '1' : '';
      });
      container.appendChild(copy);
      sync();
    });
    container.addEventListener('click', event => {
      const button = event.target.closest('.remove-pieza');
      const row = button?.closest('.pieza-form');
      if (!row || !container.contains(row) || rows().length <= 1) return;
      row.remove();
      sync();
    });
    sync();
  }
  window.CutlessPieceForms = {reindex, init};
})();
