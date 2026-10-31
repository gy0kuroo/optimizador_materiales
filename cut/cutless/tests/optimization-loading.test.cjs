const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

function setup() {
  const attrs = {}, listeners = {}, events = {}, timers = new Map(), microtasks = [];
  const classes = new Set();
  let count = 0, appended = 0, removed = 0;
  const form = {
    querySelectorAll: () => Array.from({length:20}, () => ({querySelector(selector) {
      return {value:selector.includes('cantidad') ? '5' : '25'};
    }})),
    setAttribute: (k,v) => {attrs[k]=v;}, getAttribute: k => attrs[k] ?? null,
    removeAttribute: k => {delete attrs[k];}, addEventListener: (k,v) => {listeners[k]=v;},
  };
  const background = [{inert:false}, {inert:true}];
  const nodes = {count:{textContent:''}, status:{textContent:''}, title:{focus(){}}};
  const overlay = {querySelector(selector) {return selector.includes('count') ? nodes.count : selector.includes('status') ? nodes.status : nodes.title;}, remove(){removed++;}};
  const document = {
    getElementById: () => ({content:{firstElementChild:{cloneNode:()=>overlay}}}),
    querySelectorAll: selector => selector === '.app-main, .navbar-custom' ? background : selector.includes('form[data-loading-optimization]') ? [form] : [],
    addEventListener: (k,v) => {events[k]=v;},
    body:{classList:{add:k=>classes.add(k),remove:k=>classes.delete(k)},append(){appended++;}},
  };
  const window = {addEventListener:(k,v)=>{events[k]=v;}};
  const context = {document, window, queueMicrotask:fn=>microtasks.push(fn),
    setTimeout:(fn,ms)=>{const id=++count;timers.set(id,{fn,ms});return id;},clearTimeout:id=>timers.delete(id)};
  for (const name of ['optimization-loading.js','confirmaciones.js']) vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../static/cutless/js',name),'utf8'),context);
  events.DOMContentLoaded();
  return {form,window,nodes,background,attrs,timers,events,listeners,microtasks,classes,get appended(){return appended;},get removed(){return removed;}};
}

test('100 piezas en 20 tipos se muestran sin porcentaje inventado',()=>{
  const s=setup();s.window.mostrarSkeletonOptimizacion(s.form);
  assert.equal(s.nodes.count.textContent,'100 piezas solicitadas · 20 tipos');
  assert.equal(s.attrs['aria-busy'],'true');
  assert.ok(s.background.every(n=>n.inert));
});
test('abrir dos veces no duplica la espera',()=>{
  const s=setup();s.window.mostrarSkeletonOptimizacion(s.form);s.window.mostrarSkeletonOptimizacion(s.form);
  assert.equal(s.appended,1);
});
test('una espera larga avisa sin ocultar el skeleton ni reenviar',()=>{
  const s=setup();s.window.mostrarSkeletonOptimizacion(s.form);
  const timer=[...s.timers.values()][0];assert.equal(timer.ms,20000);timer.fn();
  assert.match(s.nodes.status.textContent,/no vuelvas a enviar/);assert.equal(s.removed,0);
});
test('volver por historial restaura el formulario y el estado inert anterior',()=>{
  const s=setup();s.window.mostrarSkeletonOptimizacion(s.form);s.events.pageshow();
  assert.equal(s.removed,1);assert.equal(s.background[0].inert,false);assert.equal(s.background[1].inert,true);
  assert.equal(s.attrs['aria-busy'],undefined);assert.equal(s.timers.size,0);
});
test('un envío cancelado por validación no muestra la espera',()=>{
  const s=setup();s.listeners.submit({defaultPrevented:true});s.microtasks.forEach(fn=>fn());
  assert.equal(s.appended,0);
});
test('un envío válido muestra el skeleton y bloquea un segundo envío',()=>{
  const s=setup();s.listeners.submit({defaultPrevented:false});s.microtasks.forEach(fn=>fn());
  assert.equal(s.appended,1);let blocked=false;
  s.listeners.submit({preventDefault(){blocked=true;}});assert.equal(blocked,true);
});
