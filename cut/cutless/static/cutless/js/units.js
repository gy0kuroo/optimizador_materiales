/* Presentación de unidades. Las validaciones y conversiones del servidor siguen siendo autoritativas. */
(() => {
  'use strict';
  const factors = Object.freeze({cm:1, m:.01, mm:10, in:1/2.54, ft:1/30.48});
  const symbol = unit => Object.hasOwn(factors,unit) ? unit : 'cm';
  function fromCm(value, unit) {
    return Math.round(value * factors[symbol(unit)] * 1e6) / 1e6;
  }
  function updateMaterialOptions() {
    const unit = document.getElementById('unidad_medida_selector');
    const select = document.getElementById('material_select');
    if (!unit || !select || !window.materialData) return;
    const format = value => String(value);
    Array.from(select.options).forEach(option => {
      const material = window.materialData[option.value];
      if (!option.value || !material?.ancho || !material?.alto) return;
      option.textContent = `${material.nombre} (${format(fromCm(material.ancho,unit.value))}×${format(fromCm(material.alto,unit.value))} ${symbol(unit.value)})`;
    });
  }
  function updateLabels({materialOptions=false}={}) {
    const unit = document.getElementById('unidad_medida_selector');
    if (!unit) return;
    const text = `(${symbol(unit.value)})`;
    for (const id of ['unidad_ancho','unidad_alto']) {
      const label = document.getElementById(id);
      if (label) label.textContent = text;
    }
    document.querySelectorAll('.unidad-pieza').forEach(label => { label.textContent = text; });
    const kerf = document.querySelector('.unidad-margen');
    if (kerf) kerf.textContent = '(mm)';
    if (materialOptions) updateMaterialOptions();
  }
  window.CutlessUnits = {fromCm,symbol,updateLabels,updateMaterialOptions};
})();
