(() => {
  'use strict';
  const element = document.getElementById('modalImagen');
  if (!element) return;
  const modal = bootstrap.Modal.getOrCreateInstance(element);
  const viewport = document.getElementById('history-board-viewport');
  const canvas = document.getElementById('history-board-canvas');
  const image = document.getElementById('history-board-image');
  const status = document.getElementById('history-board-status');
  const previous = document.getElementById('history-board-previous');
  const next = document.getElementById('history-board-next');
  const zoomIn = document.getElementById('history-board-in');
  const zoomOut = document.getElementById('history-board-out');
  const fit = document.getElementById('history-board-fit');
  const position = document.getElementById('history-board-position');
  const pieces = document.getElementById('history-board-pieces');
  const details = document.getElementById('history-board-data');
  const recovery = document.getElementById('history-board-recovery');
  const login = document.getElementById('history-board-login');
  const motion = matchMedia('(prefers-reduced-motion: reduce)');
  const cache = new Map();
  let drawing = image, index = 0, total = 0, zoom = 1;
  let request = null, number = '', optimizationId = null, version = 0;
  const frame = () => new Promise(resolve => requestAnimationFrame(resolve));
  const skeleton = part => document.getElementById(`history-skeleton-${part}`).content.cloneNode(true);
  function busy(value) {
    [viewport, pieces, details].forEach(node => node.setAttribute('aria-busy', String(value)));
  }
  function controls(loading = false) {
    previous.disabled = index === 0;
    next.disabled = !total || index >= total - 1;
    zoomIn.disabled = zoomOut.disabled = fit.disabled = loading;
  }
  function loading() {
    element.classList.remove('history-legacy');
    recovery.hidden = true; login.hidden = true;
    status.setAttribute('role', 'status');
    status.textContent = `Cargando tablero ${index + 1}…`;
    position.textContent = total ? `Tablero ${index + 1} de ${total}` : 'Cargando…';
    image.hidden = true; drawing = image;
    canvas.replaceChildren(skeleton('drawing'));
    pieces.replaceChildren(skeleton('pieces'));
    details.replaceChildren(skeleton('summary'), skeleton('technical'));
    busy(true); controls(true);
  }
  function paint(reset = false) {
    const box = drawing.tagName.toLowerCase() === 'svg' ? drawing.viewBox.baseVal : null;
    const widthSource = box ? box.width : drawing.naturalWidth;
    const heightSource = box ? box.height : drawing.naturalHeight;
    if (!widthSource || drawing.hidden || viewport.getAttribute('aria-busy') === 'true') return;
    const ratio = widthSource / heightSource;
    const width = Math.max(1, Math.min(viewport.clientWidth - 32, (viewport.clientHeight - 32) * ratio));
    canvas.style.width = width * zoom + 'px'; canvas.style.height = width / ratio * zoom + 'px';
    document.getElementById('history-board-zoom').textContent = Math.round(zoom * 100) + '%';
    zoomOut.disabled = zoom <= .5; zoomIn.disabled = zoom >= 4;
    if (reset) { viewport.scrollTop = 0; viewport.scrollLeft = 0; }
  }
  async function fetchBoard(board, controller) {
    if (cache.has(board)) return cache.get(board);
    const pending = (async () => {
      const response = await fetch(`/cutless/api/tableros/${optimizationId}/?modo=visor&presentacion=horizontal&tablero=${board}`, {signal:controller.signal});
      if (response.redirected && response.url.includes('/usuarios/login/')) throw new Error('sesion');
      if (!response.ok) throw new Error([401, 403].includes(response.status) ? 'sesion' : 'carga');
      const data = await response.json();
      if (!Number.isInteger(data.total) || data.total < 1) throw new Error('carga');
      if (typeof data.panel === 'string') return {html:data.panel, total:data.total, source:null};
      // Compatibilidad con resultados antiguos sin coordenadas, sin alterar sus archivos.
      const panels = Array.isArray(data.paneles) ? data.paneles : [];
      const images = Array.isArray(data.imagenes) ? data.imagenes : [];
      const count = Math.max(panels.length, images.length);
      if (!count || board > count) throw new Error('carga');
      for (let i = 0; i < count; i++) cache.set(i + 1, Promise.resolve({
        html:panels[i] || '', source:images[i] ? `data:image/png;base64,${images[i]}` : null, total:count,
      }));
      return cache.get(board);
    })();
    cache.set(board, pending);
    try { return await pending; }
    catch (error) { if (request === controller) cache.delete(board); throw error; }
  }
  function reveal(node) {
    if (!motion.matches) node.animate([{opacity:.35},{opacity:1}], {duration:180});
  }
  function failure(error) {
    busy(false); pieces.replaceChildren(); details.replaceChildren();
    image.hidden = true; canvas.replaceChildren(image);
    controls(true); recovery.hidden = false;
    login.hidden = error.message !== 'sesion';
    status.setAttribute('role', 'alert');
    status.textContent = error.message === 'sesion'
      ? 'Tu sesión ya no está disponible. Inicia sesión de nuevo para consultar el tablero.'
      : 'No pudimos cargar el tablero. Puedes volver a intentarlo o regresar al historial.';
  }
  async function show(target) {
    if (!request || request.signal.aborted || target < 0 || (total && target >= total)) return;
    index = target; zoom = 1;
    const ticket = ++version, controller = request;
    const current = () => request === controller && !controller.signal.aborted && version === ticket;
    loading();
    try {
      const result = await fetchBoard(index + 1, controller);
      if (!current()) return;
      total = result.total;
      const documentPanel = new DOMParser().parseFromString(result.html, 'text/html');
      const svg = documentPanel.querySelector('svg.board-drawing');
      const table = documentPanel.querySelector('.cut-pieces');
      const summary = documentPanel.querySelector('.board-data');
      const sections = summary ? Array.from(summary.children) : [];
      element.classList.toggle('history-legacy', !svg);
      if (svg) {
        drawing = svg; canvas.replaceChildren(svg);
        viewport.setAttribute('aria-busy', 'false'); controls(false); paint(true); reveal(canvas);
      } else if (result.source) {
        drawing = image; canvas.replaceChildren(image);
        image.alt = `Tablero ${index + 1} de la optimización ${number}`;
        image.hidden = false; image.src = result.source;
        viewport.setAttribute('aria-busy', 'false'); controls(false);
        if (image.complete) paint(true);
      } else throw new Error('carga');
      position.textContent = `Tablero ${index + 1} de ${total}`;
      // Ceder un pintado al dibujo antes de insertar el resumen y las tablas.
      await frame(); if (!current()) return;
      if (sections[0]) details.replaceChildren(sections[0], skeleton('technical'));
      else details.replaceChildren();
      window.CutlessUtilization?.show(details, 'history', 0);
      reveal(details);
      await frame(); if (!current()) return;
      if (summary) details.replaceChildren(...sections);
      pieces.replaceChildren(...(table ? [table] : []));
      busy(false); status.textContent = ''; reveal(pieces);
      // Precargar únicamente el siguiente tablero durante esta apertura del visor.
      if (index + 1 < total) fetchBoard(index + 2, controller).catch(() => {});
    } catch (error) { if (current()) failure(error); }
  }
  image.addEventListener('load', () => { if (drawing === image && request && !request.signal.aborted) paint(true); });
  image.addEventListener('error', () => { if (drawing === image && request && !request.signal.aborted) { version++; failure(new Error('carga')); } });
  window.abrirModalImagen = (fallback, id, displayNumber) => {
    request?.abort(); request = new AbortController();
    cache.clear(); version++; total = 0; index = 0; zoom = 1; optimizationId = id;
    number = displayNumber || `OPT-${String(id).padStart(4, '0')}`;
    window.CutlessUtilization?.reset?.('history');
    document.getElementById('modalImagenLabel').textContent = `Tableros · ${number}`;
    document.getElementById('history-board-zoom').textContent = '100%';
    modal.show(); return show(0);
  };
  previous.addEventListener('click', () => show(index - 1));
  next.addEventListener('click', () => show(index + 1));
  document.getElementById('history-board-retry').addEventListener('click', () => { cache.delete(index + 1); show(index); });
  function changeZoom(delta) {
    const old = zoom, x = viewport.scrollLeft + viewport.clientWidth / 2, y = viewport.scrollTop + viewport.clientHeight / 2;
    zoom = Math.max(.5, Math.min(4, zoom + delta)); paint();
    viewport.scrollLeft = x * zoom / old - viewport.clientWidth / 2;
    viewport.scrollTop = y * zoom / old - viewport.clientHeight / 2;
  }
  zoomIn.addEventListener('click', () => changeZoom(.25)); zoomOut.addEventListener('click', () => changeZoom(-.25));
  fit.addEventListener('click', () => { zoom = 1; paint(true); });
  element.addEventListener('shown.bs.modal', () => paint(true));
  element.addEventListener('hide.bs.modal', () => { request?.abort(); version++; window.CutlessUtilization?.reset?.('history'); });
  element.addEventListener('hidden.bs.modal', () => { cache.clear(); busy(false); image.hidden = true; drawing = image; canvas.replaceChildren(image); pieces.replaceChildren(); details.replaceChildren(); });
  window.addEventListener('resize', () => { if (element.classList.contains('show')) paint(); });
})();
