const {test} = require('node:test');
const assert = require('node:assert/strict');
const {readFileSync} = require('node:fs');
const {resolve} = require('node:path');
const vm = require('node:vm');

function setup(mobile=true, initialInert=false) {
  const classes=new Set(), styles=new Map(), events=new Map(), menuEvents=new Map();
  const main={inert:initialInert};
  const media={matches:mobile,addEventListener(_,fn){this.change=fn;}};
  const root={classList:{add:c=>classes.add(c),remove:c=>classes.delete(c)},
    style:{setProperty:(k,v)=>styles.set(k,v),removeProperty:k=>styles.delete(k)}};
  const menu={classList:{contains:()=>true},addEventListener:(name,fn)=>menuEvents.set(name,fn)};
  const window={scrollY:350,addEventListener:(name,fn)=>events.set(name,fn),
    scrollTo(value){this.restored=value.top;}};
  vm.runInNewContext(readFileSync(resolve(__dirname,'../../static/cutless/js/mobile-navigation.js'),'utf8'),{
    window,matchMedia:()=>media,bootstrap:{Collapse:{getOrCreateInstance:()=>({hide(){}})}},
    document:{documentElement:root,getElementById:()=>menu,
      querySelector:()=>main,addEventListener:(name,fn)=>events.set(name,fn)}});
  return {classes,styles,main,media,window,menu,emit:name=>menuEvents.get(name)({target:menu}),events};
}

test('en móvil bloquea el fondo y restaura la posición al terminar el cierre',()=>{
  const env=setup();env.emit('show.bs.collapse');
  assert.equal(env.classes.has('mobile-nav-open'),true);
  assert.equal(env.styles.get('--mobile-scroll-offset'),'-350px');
  assert.equal(env.main.inert,true);
  env.emit('hidden.bs.collapse');
  assert.equal(env.classes.has('mobile-nav-open'),false);
  assert.equal(env.main.inert,false);
  assert.equal(env.window.restored,350);
});

test('en escritorio no bloquea ni cambia el desplazamiento',()=>{
  const env=setup(false);env.emit('show.bs.collapse');env.emit('hidden.bs.collapse');
  assert.equal(env.classes.size,0);
  assert.equal(env.main.inert,false);
  assert.equal(env.window.restored,undefined);
});

test('cambiar de móvil a escritorio libera un menú abierto',()=>{
  const env=setup();env.emit('show.bs.collapse');env.media.matches=false;env.media.change();
  assert.equal(env.classes.size,0);
  assert.equal(env.main.inert,false);
  assert.equal(env.window.restored,350);
});

test('conserva una restricción de foco previa y libera al abandonar la página',()=>{
  const env=setup(true,true);env.emit('show.bs.collapse');env.events.get('pagehide')();
  assert.equal(env.main.inert,true);
  assert.equal(env.classes.size,0);
});
