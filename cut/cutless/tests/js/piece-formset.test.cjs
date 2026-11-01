const {test} = require('node:test');
const assert = require('node:assert/strict');
const {readFileSync} = require('node:fs');
const {resolve} = require('node:path');
const vm = require('node:vm');
const context = {window:{}};
vm.runInNewContext(readFileSync(resolve(__dirname,'../../static/cutless/js/piece-formset.js'),'utf8'),context);
const reindex = context.window.CutlessPieceForms.reindex;

function element(attributes, value) {
  return {attributes:{...attributes},value,
    getAttribute(name){return this.attributes[name] ?? null;},
    setAttribute(name,value){this.attributes[name]=value;}};
}
function row(index, labelIndex=index) {
  const fields=['nombre','ancho','alto','cantidad'].map(name=>element({
    name:`form-${index}-${name}`, id:`id_form-${index}-${name}`,
    'aria-describedby':`id_form-${index}-${name}_help id_form-${index}-${name}_errors`,
  },`${name}-conservado`));
  const labels=['nombre','ancho','alto','cantidad'].map(name=>element({for:`id_form-${labelIndex}-${name}`}));
  const help=element({id:`id_form-${index}-ancho_help`});
  return {fields,labels,help,querySelectorAll:()=>[...fields,...labels,help]};
}

test('cada etiqueta clonada apunta al campo de su propia fila',()=>{
  const rows=[row(0),row(1,0),row(2,0)];
  assert.equal(reindex({querySelectorAll:()=>rows}),3);
  rows.forEach(r=>r.fields.forEach((field,i)=>assert.equal(r.labels[i].attributes.for,field.attributes.id)));
});

test('eliminar una fila intermedia y añadir otra no duplica IDs ni pierde datos',()=>{
  const rows=[row(0),row(2),row(2,0)];
  reindex({querySelectorAll:()=>rows});
  const ids=rows.flatMap(r=>r.fields.map(f=>f.attributes.id));
  assert.equal(new Set(ids).size,12);
  assert.equal(rows[1].fields[1].attributes.name,'form-1-ancho');
  assert.equal(rows[1].fields[1].value,'ancho-conservado');
  assert.equal(rows[1].fields[1].attributes['aria-describedby'],'id_form-1-ancho_help id_form-1-ancho_errors');
  assert.equal(rows[1].help.attributes.id,'id_form-1-ancho_help');
});

test('si se elimina la primera fila, la siguiente conserva sus valores y se convierte en la primera',()=>{
  const remaining=row(1);reindex({querySelectorAll:()=>[remaining]});
  assert.equal(remaining.fields[3].attributes.name,'form-0-cantidad');
  assert.equal(remaining.fields[3].value,'cantidad-conservado');
  assert.equal(remaining.labels[3].attributes.for,'id_form-0-cantidad');
});

function editor(count=1) {
  const rows=[], addHandlers=[], removeHandlers=[];
  let removedErrors=0;
  function makeRow(index) {
    const r=row(index);
    r.fields.forEach(field=>{
      field.type='text';
      Object.defineProperty(field,'name',{get:()=>field.attributes.name});
    });
    r.number={textContent:''};
    r.button={hidden:false,classList:{toggle(name,value){r.button.hidden=value;}},closest:()=>r};
    r.querySelectorAll=selector=>selector==='input, select, textarea' ? r.fields : selector==='.text-danger, .alert-danger' ? [{remove(){removedErrors++;}}] : [...r.fields,...r.labels,r.help];
    r.cloneNode=()=>makeRow(0);
    r.remove=()=>rows.splice(rows.indexOf(r),1);
    return r;
  }
  for(let i=0;i<count;i++)rows.push(makeRow(i));
  const container={querySelectorAll:selector=>selector==='.pieza-form' ? rows : selector==='.pieza-numero' ? rows.map(r=>r.number) : rows.map(r=>r.button),
    addEventListener:(name,fn)=>removeHandlers.push(fn),appendChild:r=>rows.push(r),contains:r=>rows.includes(r)};
  const add={addEventListener:(name,fn)=>addHandlers.push(fn)},total={value:count};
  return {rows,container,add,total,addHandlers,removeHandlers,get removedErrors(){return removedErrors;}};
}
const init=context.window.CutlessPieceForms.init;
test('inicializar dos veces no duplica eventos; añadir limpia datos y conserva las filas previas',async()=>{
  const e=editor();init(e.container,e.add,e.total);init(e.container,e.add,e.total);
  assert.equal(e.addHandlers.length,1);assert.equal(e.removeHandlers.length,1);
  assert.equal(e.rows[0].button.hidden,true);
  await e.addHandlers[0]();
  assert.equal(e.total.value,2);assert.equal(e.rows[1].fields[3].value,'1');
  assert.equal(e.rows[1].fields[0].value,'');assert.equal(e.rows[0].fields[0].value,'nombre-conservado');
  assert.equal(e.removedErrors,1);assert.equal(e.rows[1].labels[1].attributes.for,e.rows[1].fields[1].attributes.id);
  assert.ok(e.rows.every(r=>!r.button.hidden));
});
test('el evento de eliminar reindexa y no permite retirar la última fila',()=>{
  const e=editor(3);init(e.container,e.add,e.total);
  const click=r=>e.removeHandlers[0]({target:{closest:()=>r.button}});
  click(e.rows[1]);assert.equal(e.total.value,2);
  assert.equal(e.rows[1].fields[1].attributes.name,'form-1-ancho');
  click(e.rows[0]);click(e.rows[0]);
  assert.equal(e.total.value,1);assert.equal(e.rows[0].button.hidden,true);
});
test('el límite se aplica a tipos de pieza, no a la cantidad de unidades',async()=>{
  const e=editor(20);let message;
  context.window.cutlessAlerta=async options=>{message=options.mensaje;};
  init(e.container,e.add,e.total);await e.addHandlers[0]();
  assert.equal(e.rows.length,20);assert.equal(message,'Puedes añadir hasta 20 tipos de pieza.');
});
