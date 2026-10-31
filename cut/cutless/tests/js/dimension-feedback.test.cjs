const {test} = require('node:test');
const assert = require('node:assert/strict');
const {range, help, error, renderFeedback} = require('../../static/cutless/js/dimension-feedback.js');

test('corregir elimina el nodo del aviso y su icono, y permite mostrar un error nuevo', () => {
  let node = null;
  const classes = new Set();
  const attrs = {};
  const field = {
    parentElement: {querySelector: () => node, append: value => {node = value;}},
    ownerDocument: {createElement: () => ({setAttribute() {}, remove() {node = null;}})},
    classList: {add: value => classes.add(value), remove: value => classes.delete(value)},
    setAttribute: (name, value) => {attrs[name] = value;},
  };
  renderFeedback(field, 'Valor fuera de rango', true);
  assert.equal(node.textContent, 'Valor fuera de rango');
  assert.ok(classes.has('is-invalid'));
  renderFeedback(field, '', false);
  assert.equal(node, null, 'no debe quedar un nodo vacío con icono CSS');
  assert.equal(classes.has('is-invalid'), false);
  assert.equal(attrs['aria-invalid'], 'false');
  renderFeedback(field, 'Nuevo error', true);
  assert.equal(node.textContent, 'Nuevo error');
  renderFeedback(field, '', true);
  assert.equal(node, null);
});

test('cantidad acepta enteros de 1 a 100 y rechaza excesos, negativos y fracciones', () => {
  for (const value of ['1', '50', '100', '']) assert.equal(error(value, 'cantidad'), '');
  for (const value of ['0', '-1', '101', '1246545654']) assert.match(error(value, 'cantidad'), /fuera de rango.*1 a 100/);
  for (const value of ['1.5', 'abc', 'Infinity']) assert.match(error(value, 'cantidad'), /número entero/);
});

test('explica mil metros y convierte rangos de tablero y piezas', () => {
  assert.match(error('1000', 'tablero', 'm', 'ancho'), /1000 m.*de 0,1 a 3 m/);
  assert.deepEqual(range('tablero', 'mm'), {min: 100, max: 3000});
  assert.deepEqual(range('pieza', 'm'), {min: .001, max: 3});
  assert.match(help('tablero', 'in'), /118,110236 in/);
});
test('sierra limita de 0 a 10 mm sin depender de la unidad del tablero', () => {
  for (const unit of ['cm', 'm', 'mm', 'in', 'ft']) {
    for (const value of ['0', '3', '10', '']) assert.equal(error(value, 'sierra', unit, 'ancho'), '');
    assert.match(error('11', 'sierra', unit, 'ancho'), /ingresaste 11 mm.*de 0 a 10 mm/);
    assert.match(error('-1', 'sierra', unit, 'ancho'), /demasiado bajo/);
    assert.match(error('abc', 'sierra', unit, 'ancho'), /número válido/);
    assert.deepEqual(range('sierra', unit), {min: 0, max: 10});
  }
});
test('acepta medidas físicas equivalentes en las cinco unidades', () => {
  for (const [unit, value] of [['cm', '122'], ['m', '1.22'], ['mm', '1220'], ['in', '48.031496'], ['ft', '4.002625']]) {
    assert.equal(error(value, 'tablero', unit, 'ancho'), '');
  }
  assert.equal(error('1000', 'pieza', 'mm', 'alto'), '');
  assert.match(error('1000', 'pieza', 'm', 'alto'), /demasiado alto/);
  assert.match(error('-1', 'tablero', 'cm', 'ancho'), /demasiado bajo/);
});
