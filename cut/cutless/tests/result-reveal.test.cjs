const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
function run({mobile=false,reduced=false,pending=true}={}) {
  const classes = new Set(pending ? ['optimization-result-enter'] : []), timers=[], frames=[], events={};
  const page={};
  const stages=['header','total','navigation','drawing','summary','pieces','technical','fold','costs','actions'];
  const nodes=stages.map(stage=>({dataset:{resultStage:stage},style:{setProperty(k,v){this[k]=v;}},
    closest:()=>null,querySelector:()=>null,append(node){this.overlay=node;}}));
  const root={classList:{contains:k=>classes.has(k),add:k=>classes.add(k),remove:(...ks)=>ks.forEach(k=>classes.delete(k))}};
  const document={documentElement:root,readyState:'complete',querySelector:selector=>selector.includes('template') ? {content:{cloneNode:()=>({})}} : selector==='.board-page' ? page : null,
    querySelectorAll:()=>nodes,createElement:()=>({childElementCount:0,setAttribute(){},append(){},querySelectorAll:()=>[],remove(){this.removed=true;}})};
  const window={addEventListener:(k,fn)=>events[k]=fn};
  vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../static/cutless/js/result-reveal.js'),'utf8'),{
    document,window,matchMedia:q=>({matches:q.includes('reduced') ? reduced : mobile}),requestAnimationFrame:fn=>frames.push(fn),
    setTimeout:(fn,ms)=>{timers.push({fn,ms});return timers.length;},clearTimeout(){}});
  while(frames.length)frames.shift()();
  return {nodes,classes,timers,events};
}
test('secuencia superior a inferior en escritorio, agrupando dibujo y resumen',()=>{
  const s=run(), delay=stage=>parseInt(s.nodes.find(n=>n.dataset.resultStage===stage).style['--result-delay']);
  assert.ok(delay('header')<delay('total') && delay('total')<delay('navigation'));
  assert.equal(delay('drawing'),delay('summary'));
  assert.equal(delay('pieces'),delay('technical'));
  assert.ok(delay('technical')<delay('fold') && delay('fold')<delay('costs') && delay('costs')<delay('actions'));
  assert.ok(delay('actions')+270<=1000);
  assert.ok(s.classes.has('optimization-result-ready'));
  s.timers[0].fn();
  assert.equal(s.classes.size,0);assert.ok(s.nodes.every(n=>n.overlay.removed));
});
test('en móvil piezas aparece antes que el resumen',()=>{
  const s=run({mobile:true}), get=k=>s.nodes.find(n=>n.dataset.resultStage===k).style['--result-delay'];
  assert.ok(parseInt(get('pieces'))<parseInt(get('summary')));
});
test('movimiento reducido y entradas desde historial no crean overlays',()=>{
  for(const options of [{reduced:true},{pending:false}]){
    const s=run(options);assert.ok(s.nodes.every(n=>!n.overlay));assert.equal(s.timers.length,0);
  }
});
test('salir durante la secuencia restaura el contenido',()=>{
  const s=run();s.events.pagehide();assert.equal(s.classes.size,0);assert.ok(s.nodes.every(n=>n.overlay.removed));
});
