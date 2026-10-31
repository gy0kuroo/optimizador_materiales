/* Mejora progresiva: el servidor sigue validando el formato persistido. */
(() => {
  const source = document.getElementById('id_piezas');
  if (!source) return;
  const unit = document.getElementById('id_unidad_medida');
  const panel = document.createElement('section');
  panel.className = 'template-piece-editor';
  const note = document.createElement('p');
  note.textContent = 'Añade hasta 20 tipos de pieza. Las medidas usan la unidad seleccionada; cantidad de 1 a 100.';
  const rows = document.createElement('div');
  const add = document.createElement('button');
  add.type = 'button'; add.className = 'btn btn-secondary'; add.textContent = 'Añadir tipo de pieza';
  const sync = () => {
    source.value = Array.from(rows.children).map(row => Array.from(row.querySelectorAll('input')).map(input => input.value.trim()).join(',')).join('\n');
    add.disabled = rows.children.length >= 20;
  };
  function create(values = ['', '', '', '1']) {
    const row = document.createElement('fieldset'); row.className = 'card p-3 mb-3';
    const legend = document.createElement('legend'); legend.className = 'h6'; row.append(legend);
    const grid = document.createElement('div'); grid.className = 'row g-3'; row.append(grid);
    ['Nombre de la pieza', 'Ancho', 'Alto', 'Cantidad'].forEach((text, index) => {
      const label = document.createElement('label'); label.className = 'col-md-3 form-label'; label.append(document.createTextNode(text));
      const input = document.createElement('input'); input.className = 'form-control'; input.required = true;
      input.type = index ? 'number' : 'text'; input.value = values[index] || '';
      if (index) { input.min = index === 3 ? '1' : '0.000001'; input.step = index === 3 ? '1' : 'any'; }
      if (index === 3) input.max = '100';
      if (!index) { input.maxLength = 50; input.pattern = '[^,\\r\\n]+'; }
      if (index === 1 || index === 2) input.dataset.dimension = 'true';
      input.addEventListener('input', sync); label.append(input); grid.append(label);
    });
    const remove = document.createElement('button'); remove.type = 'button'; remove.className = 'btn btn-outline-danger align-self-end mt-3'; remove.dataset.action = 'delete'; remove.dataset.icon = 'trash'; remove.textContent = 'Eliminar';
    remove.addEventListener('click', () => { row.remove(); renumber(); sync(); }); row.append(remove); rows.append(row); renumber(); updateUnits();
  }
  function renumber() { Array.from(rows.children).forEach((row, i) => { row.querySelector('legend').textContent = `Tipo de pieza ${i + 1}`; }); }
  function updateUnits() {
    const key = unit ? unit.value : 'cm';
    const factor = {cm: 1, m: 100, in: 2.54, ft: 30.48}[key] || 1;
    rows.querySelectorAll('[data-dimension]').forEach(input => {
      input.min = String(Math.ceil(.1 / factor * 1000000) / 1000000);
      input.max = String(Math.floor(300 / factor * 1000000) / 1000000);
      input.parentElement.firstChild.textContent = (input.parentElement.firstChild.textContent.startsWith('Ancho') ? 'Ancho' : 'Alto') + ` (${key})`;
    });
  }
  if (unit) unit.addEventListener('change', updateUnits);
  const lines = source.value.trim().split(/\r?\n/).filter(Boolean);
  // Si hay datos antiguos mal formados, conservar el editor original para corregirlos.
  if (lines.some(line => line.split(',').length !== 4) || lines.length > 20) return;
  lines.forEach(line => create(line.split(',')));
  if (!lines.length) create();
  add.addEventListener('click', () => { if (rows.children.length < 20) { create(); sync(); rows.lastElementChild.querySelector('input').focus(); } });
  source.hidden = true; source.required = false;
  const title = document.querySelector('label[for="id_piezas"]'); if (title) title.textContent = 'Piezas de la plantilla *';
  panel.append(note, rows, add); source.after(panel);
  const format = source.parentElement.querySelector('.template-format'); if (format) format.hidden = true;
  source.form.addEventListener('submit', sync);
})();
