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
  const normalize = text => text.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  let page = 1;
  function render() {
    const term = normalize(search.value.trim());
    const filtered = rows.filter(row => normalize(row.dataset.search).includes(term));
    const pages = Math.max(1, Math.ceil(filtered.length / 6));
    page = Math.max(1, Math.min(page, pages));
    const visible = new Set(filtered.slice((page - 1) * 6, page * 6));
    rows.forEach(row => { row.hidden = !visible.has(row); });
    previous.disabled = page === 1; next.disabled = page === pages;
    label.textContent = `Página ${page} de ${pages} · ${filtered.length} ${filtered.length === 1 ? "resultado" : "resultados"}`;
    root.querySelector('#budget-no-matches').hidden = filtered.length !== 0 || rows.length === 0;
    const selected = rows.filter(row => row.querySelector('input').checked).length;
    count.textContent = `${selected} ${selected === 1 ? 'seleccionada' : 'seleccionadas'} en total`;
  }
  previous.addEventListener('click', () => { page--; render(); });
  next.addEventListener('click', () => { page++; render(); });
  search.addEventListener('input', () => { page = 1; render(); });
  search.addEventListener('keydown', event => { if (event.key === 'Enter') event.preventDefault(); });
  root.addEventListener('change', render);
  root.querySelector('.budget-selector-tools').hidden = false;
  render();
})();
