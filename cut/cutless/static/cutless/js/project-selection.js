/* El servidor conserva la selección al paginar, incluso sin JavaScript. */
(() => {
  const all = document.getElementById('select-all');
  const count = document.getElementById('selection-count');
  if (!all || !count) return;
  const boxes = Array.from(document.querySelectorAll('.optimizacion-checkbox'));
  const preserved = document.querySelectorAll('.selection-preserved').length;
  function update() {
    const selected = boxes.filter(box => box.checked).length;
    all.checked = boxes.length > 0 && selected === boxes.length;
    all.indeterminate = selected > 0 && selected < boxes.length;
    all.disabled = boxes.length === 0;
    count.textContent = `${preserved + selected} ${preserved + selected === 1 ? "seleccionada" : "seleccionadas"}`;
  }
  all.addEventListener('change', () => { boxes.forEach(box => { box.checked = all.checked; }); update(); });
  boxes.forEach(box => box.addEventListener('change', update));
  const search = document.getElementById('project-plan-search');
  search?.addEventListener('keydown', event => {
    if (event.key === 'Enter') {
      event.preventDefault();
      search.form.requestSubmit(search.form.querySelector('[value="buscar"]'));
    }
  });
  update();
})();
