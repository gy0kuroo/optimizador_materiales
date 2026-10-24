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
  const pieces = document.getElementById('history-board-pieces');
  const details = document.getElementById('history-board-data');
  let panels = [], drawing = image;
  let sources = [], index = 0, zoom = 1, request = null, number = '';

  function paint(reset = false) {
    const box = drawing.tagName.toLowerCase() === 'svg' ? drawing.viewBox.baseVal : null;
    const widthSource = box ? box.width : drawing.naturalWidth;
    const heightSource = box ? box.height : drawing.naturalHeight;
    if (!widthSource || drawing.hidden) return;
    const ratio = widthSource / heightSource;
    const width = Math.max(1, Math.min(viewport.clientWidth - 32, (viewport.clientHeight - 32) * ratio));
    canvas.style.width = width * zoom + 'px';
    canvas.style.height = width / ratio * zoom + 'px';
    document.getElementById('history-board-zoom').textContent = Math.round(zoom * 100) + '%';
    zoomOut.disabled = zoom <= .5;
    zoomIn.disabled = zoom >= 4;
    if (reset) { viewport.scrollTop = 0; viewport.scrollLeft = 0; }
  }
  function render() {
    if (!matchMedia('(prefers-reduced-motion: reduce)').matches) viewport.animate([{opacity:.2},{opacity:1}], {duration:220});
    zoom = 1;
    previous.disabled = index === 0;
    next.disabled = index === sources.length - 1;
    document.getElementById('history-board-position').textContent = `Tablero ${index + 1} de ${sources.length}`;
    document.getElementById('modalImagenLabel').textContent = `Optimización ${number}`;
    pieces.replaceChildren(); details.replaceChildren();
    element.classList.toggle('history-legacy', !panels[index]);
    if (panels[index]) {
      const panel = new DOMParser().parseFromString(panels[index], 'text/html');
      const svg = panel.querySelector('svg.board-drawing');
      const table = panel.querySelector('.cut-pieces');
      const summary = panel.querySelector('.board-data');
      if (table) pieces.append(table);
      if (summary) details.append(summary);
      if (svg) {
        drawing = svg; canvas.replaceChildren(svg);
        status.textContent = ''; paint(true); return;
      }
    }
    drawing = image; canvas.replaceChildren(image);
    image.alt = `Tablero ${index + 1} de la optimización ${number}`;
    image.hidden = false;
    image.src = sources[index];
    if (image.complete) paint(true);
  }
  image.addEventListener('load', () => { status.textContent = ''; paint(true); });
  image.addEventListener('error', () => {
    image.hidden = true;
    status.textContent = 'No se pudo cargar la imagen del tablero. Vuelve al historial y abre el resultado para revisarlo.';
  });
  window.abrirModalImagen = async (fallback, id, displayNumber) => {
    request?.abort();
    const controller = new AbortController();
    request = controller;
    number = displayNumber || `OPT-${String(id).padStart(4, '0')}`;
    sources = []; panels = []; index = 0; zoom = 1;
    pieces.replaceChildren(); details.replaceChildren();
    drawing = image; canvas.replaceChildren(image);
    image.hidden = true;
    status.textContent = 'Cargando tableros…';
    previous.disabled = next.disabled = zoomIn.disabled = zoomOut.disabled = true;
    document.getElementById('history-board-position').textContent = 'Cargando…';
    document.getElementById('history-board-zoom').textContent = '100%';
    document.getElementById('modalImagenLabel').textContent = `Tableros · ${number}`;
    modal.show();
    try {
      const response = await fetch(`/cutless/api/tableros/${id}/?presentacion=horizontal`, {signal: controller.signal});
      if (!response.ok) throw new Error('No disponible');
      const data = await response.json();
      if (controller.signal.aborted) return;
      panels = Array.isArray(data.paneles) ? data.paneles : [];
      sources = Array.isArray(data.imagenes) ? data.imagenes.map(value => `data:image/png;base64,${value}`) : [];
    } catch (error) {
      if (controller.signal.aborted) return;
    }
    if (controller.signal.aborted) return;
    if (!sources.length) sources = [fallback];
    render();
  };
  previous.addEventListener('click', () => { if (index > 0) { index--; render(); } });
  next.addEventListener('click', () => { if (index < sources.length - 1) { index++; render(); } });
  function changeZoom(delta) {
    const old = zoom;
    const x = viewport.scrollLeft + viewport.clientWidth / 2;
    const y = viewport.scrollTop + viewport.clientHeight / 2;
    zoom = Math.max(.5, Math.min(4, zoom + delta));
    paint();
    viewport.scrollLeft = x * zoom / old - viewport.clientWidth / 2;
    viewport.scrollTop = y * zoom / old - viewport.clientHeight / 2;
  }
  zoomIn.addEventListener('click', () => changeZoom(.25));
  zoomOut.addEventListener('click', () => changeZoom(-.25));
  document.getElementById('history-board-fit').addEventListener('click', () => { zoom = 1; paint(true); });
  element.addEventListener('shown.bs.modal', () => paint(true));
  element.addEventListener('hidden.bs.modal', () => { request?.abort(); image.hidden = true; drawing = image; canvas.replaceChildren(image); pieces.replaceChildren(); details.replaceChildren(); });
  window.addEventListener('resize', () => { if (element.classList.contains('show')) paint(); });
})();
