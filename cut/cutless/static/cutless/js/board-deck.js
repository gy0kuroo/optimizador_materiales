/* Navegación de presentación: conserva los planos, las piezas y sus datos originales. */
(() => {
  'use strict';
  const deck = document.querySelector('[data-board-deck]');
  if (!deck) return;
  const pages = Array.from(deck.querySelectorAll('.board-page'));
  const previous = document.getElementById('deck-previous');
  const next = document.getElementById('deck-next');
  const position = document.getElementById('deck-position');
  if (!pages.length) return;
  let current = 0;
  function select(index) {
    if (!Number.isInteger(index) || index < 0 || index >= pages.length) return;
    current = index;
    pages.forEach((page, number) => { page.hidden = number !== current; });
    if (!matchMedia('(prefers-reduced-motion: reduce)').matches) {
      pages[current].animate([{opacity:.2}, {opacity:1}], {duration:220, easing:'ease-out'});
    }
    window.CutlessUtilization?.show(pages[current], 'deck');
    position.textContent = `Tablero ${current + 1} de ${pages.length}`;
    previous.disabled = current === 0;
    next.disabled = current === pages.length - 1;
  }
  previous.addEventListener('click', () => select(current - 1));
  next.addEventListener('click', () => select(current + 1));
  // Al recorrer el visor ampliado, el mismo tablero queda visible al cerrarlo.
  document.addEventListener('cutless:board-selected', event => select(event.detail.index));
  deck.querySelector('.board-deck-controls').hidden = false;
  deck.classList.add('board-deck-ready');
  select(0);
})();
