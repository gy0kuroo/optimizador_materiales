/* El menú plegable desplaza sus opciones, nunca la página que hay detrás. */
(() => {
  'use strict';
  const menu = document.getElementById('navbarNav');
  if (!menu) return;
  const narrow = matchMedia('(max-width: 1199px)');
  const main = document.querySelector('.app-main');
  let scroll = null, previousInert = false;
  function lock() {
    if (!narrow.matches || scroll !== null) return;
    scroll = window.scrollY;
    previousInert = main?.inert || false;
    document.documentElement.style.setProperty('--mobile-scroll-offset', `${-scroll}px`);
    document.documentElement.classList.add('mobile-nav-open');
    if (main) main.inert = true;
  }
  function unlock() {
    if (scroll === null) return;
    const restore = scroll; scroll = null;
    document.documentElement.classList.remove('mobile-nav-open');
    document.documentElement.style.removeProperty('--mobile-scroll-offset');
    if (main) main.inert = previousInert;
    window.scrollTo({top:restore, left:0, behavior:'instant'});
  }
  menu.addEventListener('show.bs.collapse', event => { if (event.target === menu) lock(); });
  menu.addEventListener('hidden.bs.collapse', event => { if (event.target === menu) unlock(); });
  menu.addEventListener('click', event => {
    if (narrow.matches && event.target.closest('a[href], #btn-tutorial')) bootstrap.Collapse.getOrCreateInstance(menu).hide();
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && scroll !== null) {
      bootstrap.Collapse.getOrCreateInstance(menu).hide();
      document.querySelector('[data-bs-target="#navbarNav"]')?.focus();
    }
  });
  narrow.addEventListener('change', () => {
    if (!narrow.matches) unlock();
    else if (menu.classList.contains('show')) lock();
  });
  window.addEventListener('pagehide', unlock);
  window.addEventListener('pageshow', () => { if (menu.classList.contains('show')) lock(); });
})();
