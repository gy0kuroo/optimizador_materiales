/* Volver desde la caché del historial debe abrir un formulario GET vigente. */
(() => {
  window.addEventListener('pageshow', event => {
    if (event.persisted) window.location.replace(window.location.href);
  });
})();
