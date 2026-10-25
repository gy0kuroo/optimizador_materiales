const {test} = require('node:test');
const assert = require('node:assert/strict');
const {readFileSync} = require('node:fs');
const {resolve} = require('node:path');
const vm = require('node:vm');

function environment(reduced = false) {
  let now = 0, id = 0;
  const frames = new Map();
  const motion = {matches: reduced};
  const context = {window: {}, document: {querySelector: () => null},
    matchMedia: () => motion, performance: {now: () => now},
    requestAnimationFrame: fn => { frames.set(++id, fn); return id; },
    cancelAnimationFrame: key => frames.delete(key)};
  vm.runInNewContext(readFileSync(resolve(__dirname, '../../static/cutless/js/utilization.js'), 'utf8'), context);
  return {show: context.window.CutlessUtilization.show, motion, frames,
    advance(time) { now = time; const pending = [...frames.values()]; frames.clear(); pending.forEach(fn => fn(now)); }};
}

function graph(value) {
  const circle = {style: {}, setAttribute(key, value) {this[key] = value;}};
  const widget = {dataset: {utilization: String(value)}, querySelector: () => circle};
  return {querySelector: () => widget, circle};
}

test('90 → 60 interpola desde el porcentaje anterior y termina exactamente en 60', () => {
  const env = environment(), first = graph(90), next = graph(60);
  env.show(first, 'deck'); env.show(next, 'deck');
  assert.equal(next.circle['stroke-dasharray'], '90 100');
  env.advance(325);
  const middle = parseFloat(next.circle['stroke-dasharray']);
  assert.ok(middle > 60 && middle < 90);
  env.advance(650);
  assert.equal(next.circle['stroke-dasharray'], '60 100');
  assert.equal(next.circle.pathLength, '100');
  assert.equal(next.circle.style.stroke, 'rgb(116, 118, 38)');
});

test('navegación rápida continúa desde el valor visible y cancela la transición anterior', () => {
  const env = environment(), first = graph(90), second = graph(60), third = graph(80);
  env.show(first, 'viewer'); env.show(second, 'viewer'); env.advance(200);
  const visible = second.circle['stroke-dasharray'];
  env.show(third, 'viewer');
  assert.equal(third.circle['stroke-dasharray'], visible);
  assert.equal(env.frames.size, 1);
  env.advance(850);
  assert.equal(third.circle['stroke-dasharray'], '80 100');
});

test('escala roja a verde, límites y movimiento reducido', () => {
  const env = environment(true);
  for (const [value, expected, color] of [[-10, 0, 'rgb(217, 0, 0)'], [50, 50, 'rgb(145, 114, 32)'], [120, 100, 'rgb(0, 135, 61)']]) {
    const root = graph(value); env.show(root, 'history');
    assert.equal(root.circle['stroke-dasharray'], `${expected} 100`);
    assert.equal(root.circle.style.stroke, color);
  }
  assert.equal(env.frames.size, 0);
});

test('el gráfico total mantiene un estado independiente del tablero', () => {
  const env = environment(), total = graph(75), board = graph(90), next = graph(60);
  env.show(total, 'total'); env.show(board, 'deck'); env.show(next, 'deck'); env.advance(650);
  assert.equal(total.circle['stroke-dasharray'], '75 100');
  assert.equal(next.circle['stroke-dasharray'], '60 100');
});
