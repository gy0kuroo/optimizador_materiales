(() => {
    const element = document.getElementById('modalTablero');
    if (!element) return;
    const cards = Array.from(document.querySelectorAll('.board-card'));
    const modal = bootstrap.Modal.getOrCreateInstance(element, {backdrop: 'static', keyboard: false});
    const viewport = document.getElementById('board-viewport');
    const canvas = document.getElementById('board-canvas');
    const data = document.getElementById('board-viewer-data');
    const previous = document.getElementById('board-previous');
    const next = document.getElementById('board-next');
    const zoomIn = document.getElementById('board-zoom-in');
    const zoomOut = document.getElementById('board-zoom-out');
    const resultId = element.dataset.resultId;
    const stateKey = 'cutlessBoardViewer';
    let current = 0;
    let zoom = 1;
    let drawing = null;
    let opener = null;

    function dimensions() {
        if (drawing?.tagName.toLowerCase() === 'svg') {
            const box = drawing.viewBox.baseVal;
            return {width: box.width, height: box.height};
        }
        return {width: drawing?.naturalWidth || 1, height: drawing?.naturalHeight || 1};
    }

    function paint(reset = false) {
        if (!drawing) return;
        const size = dimensions();
        const ratio = size.width / size.height;
        const width = Math.max(1, Math.min(viewport.clientWidth - 32, (viewport.clientHeight - 32) * ratio));
        canvas.style.width = `${width * zoom}px`;
        canvas.style.height = `${width / ratio * zoom}px`;
        document.getElementById('board-zoom-value').textContent = `${Math.round(zoom * 100)}%`;
        zoomIn.disabled = zoom >= 4;
        zoomOut.disabled = zoom <= .5;
        if (reset) { viewport.scrollTop = 0; viewport.scrollLeft = 0; }
    }

    function render(index) {
        current = index;
        document.dispatchEvent(new CustomEvent('cutless:board-selected', {detail: {index}}));
        const card = cards[index];
        drawing = card.querySelector('.board-drawing').cloneNode(true);
        canvas.replaceChildren(drawing);
        if (!matchMedia('(prefers-reduced-motion: reduce)').matches) canvas.animate([{opacity:.2},{opacity:1}], {duration:220});
        data.replaceChildren(card.querySelector('.board-data').cloneNode(true));
        const pieces = card.querySelector('.cut-pieces');
        const canvasSection = element.querySelector('.board-canvas-section');
        canvasSection.querySelector(':scope > .cut-pieces')?.remove();
        if (pieces) canvasSection.append(pieces.cloneNode(true));
        document.getElementById('modalTableroLabel').textContent = 'Visor del tablero';
        document.getElementById('board-position').textContent = `Tablero ${index + 1} de ${cards.length}`;
        previous.disabled = index === 0;
        next.disabled = index === cards.length - 1;
        zoom = 1;
        if (drawing.tagName.toLowerCase() === 'img') drawing.addEventListener('load', () => paint(true), {once: true});
        paint(true);
    }

    function open(index, fromHistory = false) {
        if (!Number.isInteger(index) || index < 0 || index >= cards.length) return;
        opener = cards[index].querySelector('[data-open-board]');
        const alreadyOpen = element.classList.contains('show');
        render(index);
        // Una entrada de historial representa el visor completo, no cada cambio de tablero.
        if (!fromHistory) {
            const state = {...history.state, [stateKey]: {resultId, index}};
            if (alreadyOpen) history.replaceState(state, '', location.href);
            else history.pushState(state, '', location.href);
        }
        if (!alreadyOpen) modal.show();
    }

    function close() {
        if (history.state?.[stateKey]?.resultId === resultId) history.back();
        else modal.hide();
    }

    cards.forEach((card, index) => card.querySelector('[data-open-board]').addEventListener('click', () => open(index)));
    element.addEventListener('shown.bs.modal', () => paint(true));
    element.addEventListener('hidden.bs.modal', () => { drawing = null; opener?.focus(); });
    element.querySelector('[data-close-viewer]').addEventListener('click', close);
    element.addEventListener('keydown', event => {
        if (event.key === 'Escape') { event.preventDefault(); close(); }
    });
    window.addEventListener('popstate', event => {
        const state = event.state?.[stateKey];
        if (state?.resultId === resultId) open(state.index, true);
        else if (element.classList.contains('show')) modal.hide();
    });
    previous.addEventListener('click', () => open(current - 1));
    next.addEventListener('click', () => open(current + 1));
    function changeZoom(amount) {
        const oldZoom = zoom;
        const centerX = viewport.scrollLeft + viewport.clientWidth / 2;
        const centerY = viewport.scrollTop + viewport.clientHeight / 2;
        zoom = Math.min(4, Math.max(.5, zoom + amount));
        paint();
        viewport.scrollLeft = centerX * zoom / oldZoom - viewport.clientWidth / 2;
        viewport.scrollTop = centerY * zoom / oldZoom - viewport.clientHeight / 2;
    }
    zoomIn.addEventListener('click', () => changeZoom(.25));
    zoomOut.addEventListener('click', () => changeZoom(-.25));
    document.getElementById('board-fit').addEventListener('click', () => { zoom = 1; paint(true); });
    window.addEventListener('resize', () => { if (element.classList.contains('show')) paint(); });
})();
