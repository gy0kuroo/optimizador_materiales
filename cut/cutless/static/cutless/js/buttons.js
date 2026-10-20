/* Presentación de acciones estáticas y dinámicas. La semántica viene del HTML. */
(() => {
  'use strict';
  const sprite = document.body.dataset.buttonIcons;
  function icon(name) {
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.classList.add('button-icon');
    svg.setAttribute('aria-hidden', 'true');
    svg.setAttribute('focusable', 'false');
    const use = document.createElementNS(svg.namespaceURI, 'use');
    use.setAttribute('href', `${sprite}#${name}`);
    svg.append(use);
    return svg;
  }
  function decorate(button) {
    if (button.matches('.introjs-button')) {
      button.classList.add('btn');
      button.dataset.action ||= button.matches('.introjs-nextbutton,.introjs-donebutton') ? 'primary' : 'secondary';
      button.dataset.icon ||= button.matches('.introjs-prevbutton') ? 'chevron-left' : 'chevron-right';
    }
    if (!button.matches('.btn,.btn-action') || button.dataset.busy === 'true') return;
    if (button.matches('.favorito-btn')) { button.classList.add('btn-icon'); button.setAttribute('aria-label',button.title); }
    if (button.dataset.action) {
      const variant = button.dataset.action === 'delete' ? 'danger' : button.dataset.action;
      if (['primary', 'secondary', 'success', 'danger', 'text'].includes(variant)) {
        ['primary', 'secondary', 'success', 'danger', 'text'].forEach(v => button.classList.toggle(`btn-${v}`, v === variant));
      }
    }
    const name = button.dataset.icon;
    if (!name || !sprite) return;
    const existing = button.querySelector(':scope > .button-icon');
    if (existing && existing.dataset.icon === name) return;
    existing?.remove();
    const svg = icon(name); svg.dataset.icon = name;
    button.prepend(svg);
  }
  function scan(root) {
    if (!(root instanceof Element)) return;
    decorate(root);
    root.querySelectorAll('.btn,.btn-action,.introjs-button').forEach(decorate);
  }
  scan(document.body);
  new MutationObserver(records => {
    const roots = new Set();
    records.forEach(record => {
      const button = record.target instanceof Element ? record.target.closest('.btn,.btn-action') : record.target.parentElement?.closest('.btn,.btn-action');
      if (button) roots.add(button);
      record.addedNodes.forEach(node => { if (node instanceof Element) roots.add(node); });
    });
    roots.forEach(scan);
  }).observe(document.body, {childList:true, subtree:true, attributes:true, attributeFilter:['data-action','data-icon','data-favorito','title']});

  const states = new WeakMap();
  window.cutlessButtonLoading = (button, loading) => {
    if (!button) return;
    if (loading) {
      if (states.has(button)) return;
      states.set(button, {disabled:button.disabled, aria:button.getAttribute('aria-disabled'), width:button.style.width});
      button.style.width = `${button.getBoundingClientRect().width}px`;
      button.dataset.busy = 'true'; button.setAttribute('aria-busy','true'); button.setAttribute('aria-disabled','true');
      if (button.tagName === 'BUTTON') button.disabled = true;
      button.querySelector(':scope > .button-icon')?.remove();
      const spinner = document.createElement('span'); spinner.className = 'button-spinner'; spinner.setAttribute('aria-hidden','true'); button.prepend(spinner);
    } else {
      const state = states.get(button); if (!state) return;
      button.querySelector(':scope > .button-spinner')?.remove();
      button.style.width = state.width;
      if (button.tagName === 'BUTTON') button.disabled = state.disabled;
      if (state.aria === null) button.removeAttribute('aria-disabled'); else button.setAttribute('aria-disabled',state.aria);
      delete button.dataset.busy; button.removeAttribute('aria-busy'); states.delete(button); decorate(button);
    }
  };
  document.addEventListener('click', event => {
    const button = event.target.closest('.btn[aria-disabled="true"]');
    if (button) { event.preventDefault(); event.stopImmediatePropagation(); }
  }, true);
  document.addEventListener('submit', event => {
    const button = event.submitter;
    // Esperar a que termine la validación y se serialicen los campos del envío.
    setTimeout(() => {
      if (!event.defaultPrevented && button?.matches('.btn:not([data-action="delete"])')) window.cutlessButtonLoading(button,true);
    },0);
  });
  window.addEventListener('pageshow', () => document.querySelectorAll('.btn[data-busy="true"]').forEach(button => window.cutlessButtonLoading(button,false)));
})();
