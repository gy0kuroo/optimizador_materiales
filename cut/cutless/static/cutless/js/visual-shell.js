/* Estado visual del menú: no modifica destinos, permisos ni preferencias. */
(() => {
  const nav = document.querySelector('.navbar-custom');
  if (!nav) return;
  nav.querySelectorAll('a[href]').forEach(link => {
    if (new URL(link.href, location.href).pathname !== location.pathname) return;
    link.classList.add('active');
    link.setAttribute('aria-current', 'page');
    // El grupo queda abierto desde el servidor; solo el destino se destaca.
  });
})();
