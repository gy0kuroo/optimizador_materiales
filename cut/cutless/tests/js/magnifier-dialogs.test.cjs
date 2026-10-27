const {test} = require('node:test');
const assert = require('node:assert/strict');
const {readFileSync} = require('node:fs');
const {resolve} = require('node:path');
const vm = require('node:vm');

function setup() {
  const events = new Map(), state = {dialogs: [], blocked: false};
  function element() {
    return {hidden:false,style:{},dataset:{},classList:{toggle(){},contains(){return false;}},
      addEventListener(){},querySelectorAll(){return [];},contains(){return false;},
      append(child){child.parentElement=this;},setAttribute(){},replaceChildren(){}};
  }
  const body = element(), controls = element(); controls.parentElement = body;
  const ids = Object.fromEntries(['magnifier-toggle','magnifier-options','magnifier-hint','magnifier-level','magnifier-status','magnifier-lens'].map(id=>[id,element()]));
  ids['reading-magnifier']=controls;
  ids['magnifier-lens'].attachShadow=()=>element();
  const context={window:{addEventListener(){}},innerWidth:1280,innerHeight:720,
    performance:{now:()=>0},setTimeout,clearTimeout,cancelAnimationFrame(){},
    MutationObserver:class {constructor(fn){state.mutate=()=>fn([]);}observe(){}},
    document:{body,documentElement:element(),getElementById:id=>ids[id],createElement:element,
      addEventListener(name,fn){events.set(name,fn);},
      querySelectorAll:()=>state.dialogs,querySelector:()=>state.blocked?{}:null}};
  vm.runInNewContext(readFileSync(resolve(__dirname,'../../static/cutless/js/magnifier.js'),'utf8'),context);
  return {state,controls,body,emit:(name,target)=>events.get(name)({target}),
    dialog(reading=false){const toolbar=element();return {toolbar,matches:()=>reading,querySelector:()=>toolbar};}};
}

test('confirmación oculta la lupa desde la apertura hasta el cierre completo',()=>{
  const env=setup(), dialog=env.dialog();
  env.emit('show.bs.modal',dialog); env.state.mutate();
  assert.equal(env.controls.hidden,true);
  env.state.dialogs=[dialog]; env.emit('shown.bs.modal',dialog);
  assert.equal(env.controls.hidden,true);
  env.emit('hide.bs.modal',dialog); env.state.dialogs=[]; env.state.mutate();
  assert.equal(env.controls.hidden,true);
  env.emit('hidden.bs.modal',dialog);
  assert.equal(env.controls.hidden,false);
  assert.equal(env.controls.parentElement,env.body);
});

test('solo los visores de lectura reciben los controles y una confirmación anidada los oculta',()=>{
  const env=setup(), viewer=env.dialog(true), confirm=env.dialog();
  env.state.dialogs=[viewer]; env.emit('shown.bs.modal',viewer);
  assert.equal(env.controls.hidden,false);
  assert.equal(env.controls.parentElement,viewer.toolbar);
  env.emit('show.bs.modal',confirm);env.state.dialogs=[viewer,confirm];env.emit('shown.bs.modal',confirm);
  assert.equal(env.controls.hidden,true);
  env.state.dialogs=[viewer];env.emit('hidden.bs.modal',confirm);
  assert.equal(env.controls.hidden,false);
  assert.equal(env.controls.parentElement,viewer.toolbar);
});

test('pantallas de carga, tutoriales y diálogos nativos suspenden los controles',()=>{
  const env=setup();env.state.blocked=true;env.state.mutate();
  assert.equal(env.controls.hidden,true);
  env.state.blocked=false;env.state.mutate();
  assert.equal(env.controls.hidden,false);
});

test('los paneles offcanvas tampoco muestran la lupa durante su apertura',()=>{
  const env=setup(), panel=env.dialog();env.emit('show.bs.offcanvas',panel);env.state.mutate();
  assert.equal(env.controls.hidden,true);
  env.state.blocked=true;env.emit('shown.bs.offcanvas',panel);
  assert.equal(env.controls.hidden,true);
  env.state.blocked=false;env.emit('hidden.bs.offcanvas',panel);
  assert.equal(env.controls.hidden,false);
});
