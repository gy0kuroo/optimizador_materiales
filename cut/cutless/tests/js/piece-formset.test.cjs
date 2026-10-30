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
