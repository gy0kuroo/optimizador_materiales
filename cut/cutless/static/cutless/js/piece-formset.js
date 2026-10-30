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
  window.CutlessPieceForms = {reindex};
})();
