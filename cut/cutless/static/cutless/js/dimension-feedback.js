/* Explica límites en la unidad elegida; el servidor vuelve a validarlos. */
(() => {
  const factors = {cm: 1, m: 100, mm: .1, in: 2.54, ft: 30.48};
  const number = value => String(value).replace('.', ',');
  function range(kind, unit) {
    if (kind === 'cantidad') return {min: 1, max: 100};
    if (kind === 'sierra') return {min: 0, max: 10};
    const factor = factors[unit] || 1;
    return {min: Math.ceil((kind === 'pieza' ? .1 : 10) / factor * 1e6) / 1e6,
      max: Math.floor(300 / factor * 1e6) / 1e6};
  }
  function help(kind, unit) {
    if (kind === 'cantidad') return 'De 1 a 100 piezas iguales por tipo. Usa un número entero.';
    if (kind === 'sierra') return 'Rango permitido: de 0 a 10 mm. 0 significa sin separación.';
    const limits = range(kind, unit);
    return `Rango permitido: de ${number(limits.min)} a ${number(limits.max)} ${unit} por lado.`;
  }
  function error(value, kind, unit, side) {
    if (value === '') return '';
    if (kind === 'cantidad') {
      const quantity = Number(value);
      if (!Number.isFinite(quantity) || !Number.isInteger(quantity)) return `La cantidad debe ser un número entero. ${help(kind)}`;
      if (quantity < 1 || quantity > 100) return `Cantidad fuera de rango: ingresaste ${number(value)}. ${help(kind)}`;
      return '';
    }
    if (kind === 'sierra') {
      const mm = Number(value);
      if (!Number.isFinite(mm)) return 'Escribe un número válido para el ancho de sierra, en mm.';
      if (mm < 0 || mm > 10) return `El ancho de sierra es demasiado ${mm > 10 ? 'alto' : 'bajo'}: ingresaste ${number(value)} mm. ${help(kind)} Revisa el valor; este campo siempre se expresa en mm.`;
      return '';
    }
    const cm = Math.round(Number(value) * (factors[unit] || 1) * 1e6) / 1e6;
    const min = kind === 'pieza' ? .1 : 10;
    if (!Number.isFinite(cm)) return `Escribe un número válido para el ${side} del ${kind}, en ${unit}.`;
    if (cm < min - 1e-9 || cm > 300 + 1e-9) {
      return `El ${side} del ${kind} es demasiado ${cm > 300 ? 'alto' : 'bajo'}: ingresaste ${number(value)} ${unit}. ${help(kind, unit)} Revisa el valor o la unidad seleccionada.`;
    }
    return '';
  }
  function renderFeedback(field, text, show) {
    let feedback = field.parentElement.querySelector('.dimension-feedback');
    if (!text) {
      // Un nodo vacío conserva el icono generado por .text-danger::before.
      feedback?.remove();
      field.classList.remove('is-invalid');
      field.setAttribute('aria-invalid', 'false');
      return;
    }
    if (show && !feedback) {
      feedback = field.ownerDocument.createElement('div');
      feedback.className = 'text-danger dimension-feedback';
      feedback.setAttribute('aria-live', 'polite');
      field.parentElement.append(feedback);
    }
    if (feedback) feedback.textContent = text;
    if (show) {
      field.classList.add('is-invalid');
      field.setAttribute('aria-invalid', 'true');
    }
  }
  if (typeof module !== 'undefined') module.exports = {range, help, error, renderFeedback};
  if (typeof document === 'undefined') return;
  const selector = document.getElementById('unidad_medida_selector');
  if (!selector) return;
  const form = selector.form;
  const example = document.createElement('small');
  example.className = 'form-text text-muted';
  selector.insertAdjacentElement('afterend', example);
  const dimensions = () => form.querySelectorAll('#ancho_tablero, #alto_tablero, #margen_corte, input[name$="-ancho"], input[name$="-alto"], input[name$="-cantidad"]');
  function update(field, show = false) {
    const unit = selector.value || 'cm';
    const kind = field.name.endsWith('-cantidad') ? 'cantidad' : field.id === 'margen_corte' ? 'sierra' : field.closest('.pieza-form') ? 'pieza' : 'tablero';
    const side = /ancho/.test(field.name) ? 'ancho' : 'alto';
    const text = field.validity.badInput
      ? kind === 'cantidad' ? 'Escribe una cantidad entera de 1 a 100 piezas por tipo.' : kind === 'sierra' ? 'Escribe un número válido para el ancho de sierra, en mm.' : `Escribe un número válido para el ${side} del ${kind}, en ${unit}.`
      : error(field.value, kind, unit, side);
    field.setCustomValidity(text);
    const id = field.getAttribute('aria-describedby');
    const hint = id ? document.getElementById(id) : null;
    if (hint?.classList.contains('dimension-range')) hint.textContent = help(kind, unit);
    renderFeedback(field, text, show);
  }
  function refresh() {
    dimensions().forEach(field => update(field));
    form.querySelectorAll('.dimension-range').forEach(hint => {
      hint.textContent = help(hint.dataset.dimensionKind, selector.value || 'cm');
    });
    // Los ejemplos del tablero también deben corresponder a la unidad actual.
    for (const [id, cm] of [['ancho_tablero', 122], ['alto_tablero', 244]]) {
      const field = document.getElementById(id);
      if (field) field.placeholder = `Ej.: ${number(Math.round(cm / (factors[selector.value] || 1) * 1e6) / 1e6)}`;
    }
    const unit = selector.value || 'cm';
    const factor = factors[unit] || 1;
    example.textContent = `Escribe las medidas del tablero y de las piezas en ${unit}. Ejemplo: un tablero de 122 × 244 cm se ingresa como ${number(Math.round(122 / factor * 1e6) / 1e6)} × ${number(Math.round(244 / factor * 1e6) / 1e6)} ${unit}. El ancho de sierra siempre se ingresa en mm.`;
  }
  form.addEventListener('input', event => {
    if ([...dimensions()].includes(event.target)) update(event.target);
  });
  form.addEventListener('focusout', event => {
    if ([...dimensions()].includes(event.target)) update(event.target, true);
  });
  form.addEventListener('invalid', event => {
    if ([...dimensions()].includes(event.target)) update(event.target, true);
  }, true);
  // Se ejecuta después de los manejadores de conversión/materiales existentes.
  // Incluye change emitido al elegir una medida habitual o un material.
  form.addEventListener('change', () => queueMicrotask(refresh));
  new MutationObserver(refresh).observe(document.getElementById('pieza-container'), {childList: true});
  refresh();
})();
