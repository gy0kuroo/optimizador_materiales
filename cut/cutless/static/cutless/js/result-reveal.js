/* Presentación visual de datos ya recibidos. No altera solicitudes ni cálculos. */
(() => {
  'use strict';
  const root = document.documentElement;
  if (!root.classList.contains('optimization-result-enter')) return;
  const overlays = [];
  function finish() {
    root.classList.remove('optimization-result-enter', 'optimization-result-ready');
    overlays.forEach(node => node.remove());
    clearTimeout(window.cutlessRevealFallback);
  }
  window.addEventListener('pagehide', finish, {once:true});
  function start() {
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) { finish(); return; }
    try {
      const mobile = matchMedia('(max-width:1100px)').matches;
      const groups = ['notice', 'header', 'total', 'navigation', 'drawing', 'pieces', 'costs', 'fold', 'actions'];
      document.querySelectorAll('.result-page [data-result-stage]').forEach(node => {
        const page = node.closest('.board-page');
        if (page && page !== document.querySelector('.board-page')) return;
        const stage = node.dataset.resultStage;
        const template = document.querySelector(`template[data-result-placeholder="${stage}"]`);
        if (!template) return;
        const overlay = node.querySelector(':scope > .result-stage-placeholder') || document.createElement('div');
        overlay.className = 'result-stage-placeholder';
        overlay.setAttribute('aria-hidden', 'true');
        if (!overlay.childElementCount) overlay.append(template.content.cloneNode(true));
        // En la respuesta se conocen exactamente los campos condicionales.
        if (stage === 'costs') {
          overlay.querySelectorAll('[data-loading-cost]').forEach(field => {
            const key = `cost${field.dataset.loadingCost[0].toUpperCase()}${field.dataset.loadingCost.slice(1)}`;
            field.hidden = node.dataset[key] !== 'true';
          });
        }
        let index = groups.indexOf(stage);
        if (stage === 'summary') index = mobile ? 5 : 4;
        if (stage === 'technical') index = 5;
        if (mobile && stage === 'pieces') index = 4;
        node.style.setProperty('--result-delay', `${Math.max(0,index) * 85}ms`);
        node.append(overlay);
        overlays.push(overlay);
      });
      requestAnimationFrame(() => requestAnimationFrame(() => {
        if (!root.classList.contains('optimization-result-enter')) return;
        root.classList.add('optimization-result-ready');
        setTimeout(finish, 1000);
      }));
    } catch (_) { finish(); }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start, {once:true});
  else start();
})();
