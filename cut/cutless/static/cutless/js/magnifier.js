/* Copia visual aislada: no ejecuta scripts ni recibe clics o datos de formularios.
   El documento real sigue siendo el único con el que interactúa el usuario. */
(function () {
  'use strict';
  const controls = document.getElementById('reading-magnifier');
  if (!controls) return;
  const toggle = document.getElementById('magnifier-toggle');
  const options = document.getElementById('magnifier-options');
  const hint = document.getElementById('magnifier-hint');
  const level = document.getElementById('magnifier-level');
  const status = document.getElementById('magnifier-status');
  const lens = document.getElementById('magnifier-lens');
  const shadow = lens.attachShadow({mode: 'closed'});
  const scene = document.createElement('div');
  scene.style.cssText = 'position:absolute;left:0;top:0;transform-origin:0 0;pointer-events:none;';
  shadow.append(scene);
  let active = false, scale = 2, frame = 0, refreshTimer = 0;
  let lastPointerDown = -Infinity;
  let point = {x: innerWidth / 2, y: innerHeight / 2};

  function snapshot() {
    if (!active) return;
    const clonedBody = document.body.cloneNode(true);
    // Reservar el espacio de los controles integrados sin copiarlos a la lupa.
    if (controls.classList.contains('reading-magnifier--docked')) {
      const placeholder = document.createElement('div');
      const box = controls.getBoundingClientRect();
      placeholder.style.cssText = `width:${box.width}px;height:${box.height}px;flex:0 0 ${box.width}px;`;
      clonedBody.querySelector('#reading-magnifier')?.replaceWith(placeholder);
    }
    clonedBody.querySelectorAll('script, iframe, object, embed, #reading-magnifier, #magnifier-lens, [role="status"], [aria-live]').forEach(node => node.remove());
    clonedBody.setAttribute('inert', '');
    clonedBody.setAttribute('aria-hidden', 'true');
    clonedBody.querySelectorAll('*').forEach(node => {
      for (const attr of Array.from(node.attributes)) {
        if (attr.name.startsWith('on')) node.removeAttribute(attr.name);
      }
      node.removeAttribute('autofocus');
    });
    // cloneNode no refleja las propiedades actuales de formularios y canvas.
    const originalInputs = document.body.querySelectorAll('input, textarea, select');
    const copiedInputs = clonedBody.querySelectorAll('input, textarea, select');
    copiedInputs.forEach((node, index) => {
      const original = originalInputs[index];
      if (!original) return;
      if (node.matches('input[type="password"], input[type="hidden"]')) {
        node.value = ''; node.removeAttribute('value');
      } else if (node.tagName === 'SELECT') {
        node.selectedIndex = original.selectedIndex;
      } else {
        node.value = original.value;
        if ('checked' in node) node.checked = original.checked;
      }
    });
    const originalCanvases = document.body.querySelectorAll('canvas');
    clonedBody.querySelectorAll('canvas').forEach((node, index) => {
      const original = originalCanvases[index];
      if (original) node.getContext('2d')?.drawImage(original, 0, 0);
    });
    const fragment = document.createDocumentFragment();
    document.head.querySelectorAll('link[rel="stylesheet"], style').forEach(node => fragment.append(node.cloneNode(true)));
    const stableStyles = document.createElement('style');
    stableStyles.textContent = '*,*::before,*::after{animation:none!important;transition:none!important;caret-color:transparent!important}.fade-in{opacity:1!important;transform:none!important}';
    fragment.append(stableStyles);
    // Variables del tema se heredan desde la página real a través del host.
    const rect = document.body.getBoundingClientRect();
    clonedBody.style.cssText += `;position:absolute!important;left:${rect.left}px!important;top:${rect.top}px!important;width:${rect.width}px!important;margin:0!important;`;
    fragment.append(clonedBody);
    scene.replaceChildren(fragment);
    scene.style.width = innerWidth + 'px';
    scene.style.height = innerHeight + 'px';
    scene.dataset.theme = document.documentElement.dataset.theme || 'light';
    // Conservar la región visible de listas, tablas y diálogos desplazables.
    const originals = Array.from(document.body.querySelectorAll('*')).filter(node => node.scrollTop || node.scrollLeft);
    for (const original of originals) {
      if (!original.id) continue;
      const duplicate = clonedBody.querySelector('#' + CSS.escape(original.id));
      if (duplicate) { duplicate.scrollTop = original.scrollTop; duplicate.scrollLeft = original.scrollLeft; }
    }
    position();
  }

  function position() {
    frame = 0;
    if (!active) return;
    const width = lens.offsetWidth, height = lens.offsetHeight;
    // Centrar sobre el punto señalado, limitando el cuadro en los bordes.
    const left = Math.max(12, Math.min(point.x - width / 2, innerWidth - width - 12));
    const top = Math.max(12, Math.min(point.y - height / 2, innerHeight - height - 12));
    lens.style.left = left + 'px'; lens.style.top = top + 'px';
    scene.style.transform = `translate(${width / 2 - point.x * scale}px, ${height / 2 - point.y * scale}px) scale(${scale})`;
  }

  function setActive(value) {
    active = value;
    document.documentElement.classList.toggle('magnifier-active', active);
    toggle.setAttribute('aria-pressed', String(active));
    toggle.dataset.action = active ? 'primary' : 'secondary';
    options.hidden = hint.hidden = lens.hidden = !active;
    status.textContent = active ? 'Lupa activada. Mueve el cursor o usa Tab para ampliar. Escape para cerrar.' : 'Lupa desactivada.';
    if (active) snapshot();
    else {
      clearTimeout(refreshTimer); cancelAnimationFrame(frame);
      scene.replaceChildren();
    }
  }
  toggle.addEventListener('click', () => setActive(!active));
  controls.querySelectorAll('[data-magnifier-step]').forEach(button => {
    button.addEventListener('click', () => {
      scale = Math.max(1.5, Math.min(3, scale + Number(button.dataset.magnifierStep)));
      level.textContent = Math.round(scale * 100) + '%';
      controls.querySelector('[data-magnifier-step="-0.5"]').disabled = scale === 1.5;
      controls.querySelector('[data-magnifier-step="0.5"]').disabled = scale === 3;
      position();
    });
  });
  document.addEventListener('pointermove', event => {
    if (!active || controls.contains(event.target)) return;
    point = {x: event.clientX, y: event.clientY};
    if (!frame) frame = requestAnimationFrame(position);
  }, {passive: true});
  document.addEventListener('pointerdown', () => { lastPointerDown = performance.now(); }, {passive: true});
  document.addEventListener('focusin', event => {
    if (!active || controls.contains(event.target) || performance.now() - lastPointerDown < 200) return;
    const rect = event.target.getBoundingClientRect();
    point = {x: rect.left + rect.width / 2, y: rect.top + rect.height / 2};
    position();
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Tab') lastPointerDown = -Infinity;
    if (active && event.key === 'Escape') {
      event.preventDefault(); event.stopPropagation();
      setActive(false); toggle.focus();
    }
  }, true);
  // Los controles deben pertenecer al diálogo abierto para respetar su foco.
  document.addEventListener('shown.bs.modal', event => {
    controls.classList.add('reading-magnifier--docked');
    (event.target.querySelector('.board-toolbar') || event.target.querySelector('.modal-header') || event.target).append(controls);
    refresh();
  });
  document.addEventListener('hidden.bs.modal', () => {
    const remaining = document.querySelector('.modal.show');
    controls.classList.toggle('reading-magnifier--docked', Boolean(remaining));
    (remaining?.querySelector('.board-toolbar') || remaining?.querySelector('.modal-header') || remaining || document.body).append(controls);
    refresh();
  });
  function refresh() {
    if (!active) return;
    clearTimeout(refreshTimer);
    refreshTimer = setTimeout(snapshot, 120);
  }
  document.addEventListener('input', refresh, true);
  document.addEventListener('change', refresh, true);
  document.addEventListener('scroll', refresh, true);
  window.addEventListener('resize', refresh);
  new MutationObserver(records => {
    if (records.some(record => !controls.contains(record.target) && record.target !== lens)) refresh();
  }).observe(document.body, {subtree: true, childList: true, attributes: true, characterData: true});
})();
