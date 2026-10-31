/* El POST nativo sigue siendo único; este estado solo acompaña la espera real. */
(() => {
  'use strict';
  let active = null;
  // La página de destino consume esta marca antes de pintar el resultado.
  try { sessionStorage.removeItem('cutless-result-transition'); } catch (_) {}
  function hide() {
    if (!active) return;
    clearTimeout(active.timer);
    active.targets.forEach(([node, inert]) => { node.inert = inert; });
    active.form.removeAttribute('aria-busy');
    active.overlay.remove();
    document.body.classList.remove('optimization-loading-active');
    active = null;
  }
  function show(form) {
    if (active) return active.overlay;
    const template = document.getElementById('cutless-optimization-loading-template');
    if (!template) return window.mostrarIndicadorCarga('Generando el plan de corte…');
    const overlay = template.content.firstElementChild.cloneNode(true);
    let types = 0, total = 0;
    form.querySelectorAll('.pieza-form').forEach(row => {
      const width = Number(row.querySelector('[name$="-ancho"]')?.value);
      const height = Number(row.querySelector('[name$="-alto"]')?.value);
      const raw = row.querySelector('[name$="-cantidad"]')?.value;
      const quantity = raw === '' ? 1 : Number(raw);
      if (width > 0 && height > 0 && Number.isInteger(quantity) && quantity > 0) { types++; total += quantity; }
    });
    overlay.querySelector('[data-optimization-loading-count]').textContent =
      `${total} ${total === 1 ? 'pieza solicitada' : 'piezas solicitadas'} · ${types} ${types === 1 ? 'tipo' : 'tipos'}`;
    const targets = Array.from(document.querySelectorAll('.app-main, .navbar-custom')).map(node => [node, Boolean(node.inert)]);
    targets.forEach(([node]) => { node.inert = true; });
    form.setAttribute('aria-busy', 'true');
    document.body.classList.add('optimization-loading-active');
    document.body.append(overlay);
    try { sessionStorage.setItem('cutless-result-transition', String(Date.now())); } catch (_) {}
    active = {overlay, form, targets, timer:null};
    active.timer = setTimeout(() => {
      if (active?.overlay === overlay) overlay.querySelector('[data-optimization-loading-status]').textContent =
        'El cálculo está tardando más de lo habitual. Sigue en espera de la respuesta; no vuelvas a enviar el formulario.';
    }, 20000);
    overlay.querySelector('#optimization-loading-title').focus({preventScroll:true});
    return overlay;
  }
  window.mostrarSkeletonOptimizacion = show;
  window.ocultarSkeletonOptimizacion = hide;
  window.addEventListener('pageshow', hide);
  window.addEventListener('pagehide', hide);
})();
