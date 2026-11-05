/* Paginación en la misma página: nunca envía ni reinicia el presupuesto. */
(() => {
  const root = document.querySelector('.budget-plan-selector');
  if (!root) return;
  const rows = Array.from(root.querySelectorAll('[data-budget-plan]'));
  const search = root.querySelector('#budget-plan-search');
  const previous = root.querySelector('[data-budget-page="previous"]');
  const next = root.querySelector('[data-budget-page="next"]');
  const label = root.querySelector('#budget-page-label');
  const count = root.querySelector('#budget-selection-count');
  const table = root.querySelector('[data-budget-table-wrap]');
  const loading = root.querySelector('[data-budget-loading]');
  const clearButtons = Array.from(root.querySelectorAll('[data-budget-clear]'));
  const projectVariant = root.dataset.selectorVariant === 'project';
  const pageSize = Math.max(1, Number(root.dataset.pageSize) || 6);
  const normalize = text => text.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  let page = 1;
  let renderId = 0;

  function render(showLoading = false) {
    const currentRender = ++renderId;
    if (projectVariant && showLoading && table && loading) {
      table.style.minHeight = `${table.getBoundingClientRect().height}px`;
      table.setAttribute('aria-busy', 'true');
      loading.hidden = false;
    }

    const update = () => {
      if (currentRender !== renderId) return;
      const term = normalize(search.value.trim());
      const filtered = rows.filter(row => normalize(row.dataset.search).includes(term));
      const pages = Math.max(1, Math.ceil(filtered.length / pageSize));
      page = Math.max(1, Math.min(page, pages));
      const visible = new Set(filtered.slice((page - 1) * pageSize, page * pageSize));
      rows.forEach(row => { row.hidden = !visible.has(row); });
      previous.disabled = page === 1;
      next.disabled = page === pages;
      label.textContent = `Página ${page} de ${pages} · ${filtered.length} ${filtered.length === 1 ? 'resultado' : 'resultados'}`;
      root.querySelector('#budget-no-matches').hidden = filtered.length !== 0 || rows.length === 0;
      const selected = rows.filter(row => row.querySelector('input').checked).length;
      count.textContent = projectVariant
        ? `${selected} ${selected === 1 ? 'seleccionada' : 'seleccionadas'} en total`
        : `${selected} ${selected === 1 ? 'seleccionada' : 'seleccionadas'} en total`;
      clearButtons.forEach(button => { button.hidden = !term; });

      if (projectVariant && showLoading && table && loading) {
        window.setTimeout(() => {
          if (currentRender !== renderId) return;
          loading.hidden = true;
          table.removeAttribute('aria-busy');
          table.style.minHeight = '';
        }, 110);
      }
    };

    if (projectVariant && showLoading) window.requestAnimationFrame(update);
    else update();
  }

  previous.addEventListener('click', () => { page--; render(projectVariant); });
  next.addEventListener('click', () => { page++; render(projectVariant); });
  search.addEventListener('input', () => { page = 1; render(projectVariant); });
  search.addEventListener('keydown', event => { if (event.key === 'Enter') event.preventDefault(); });
  clearButtons.forEach(button => button.addEventListener('click', () => {
    search.value = '';
    page = 1;
    render(projectVariant);
    search.focus();
  }));
  root.addEventListener('change', event => {
    if (event.target.matches('.budget-plan-checkbox')) render();
  });
  root.querySelector('.budget-selector-tools').hidden = false;
  render();
})();
