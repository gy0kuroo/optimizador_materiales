const {test}=require('node:test');
const assert=require('node:assert/strict');
const {readFileSync}=require('node:fs');
const {resolve}=require('node:path');
const vm=require('node:vm');
function setup(unit='m') {
  const options=[{value:'',textContent:'Elegir material'},{value:'1',textContent:'OSB guardado'}];
  const nodes={unidad_medida_selector:{value:unit},unidad_ancho:{},unidad_alto:{},material_select:{value:'1',options}};
  const labels=[{},{}],kerf={};
  const window={materialData:{'1':{nombre:'OSB',ancho:122,alto:244,precio:12000}}};
  const document={getElementById:id=>nodes[id]||null,querySelectorAll:()=>labels,querySelector:()=>kerf};
  vm.runInNewContext(readFileSync(resolve(__dirname,'../../static/cutless/js/units.js'),'utf8'),{window,document});
  return {api:window.CutlessUnits,nodes,labels,kerf,options};
}
test('conversiones conocidas conservan seis decimales',()=>{
  const {api}=setup();
  for(const [unit,value] of [['cm',122],['m',1.22],['mm',1220],['in',48.031496],['ft',4.002625]]) assert.equal(api.fromCm(122,unit),value);
  assert.equal(api.fromCm(0,'m'),0);assert.equal(api.symbol('desconocida'),'cm');
});
test('barrido dimensional coincide con la fórmula anterior y mantiene tolerancia de 0,01 cm',()=>{
  const {api}=setup(), factors={cm:1,m:.01,mm:10,in:1/2.54,ft:1/30.48};
  for(let n=1;n<=1000;n++)for(const [unit,factor] of Object.entries(factors)){
    const cm=n*.29991, value=api.fromCm(cm,unit);
    assert.equal(value,Math.round(cm*factor*Math.pow(10,6))/Math.pow(10,6));
    assert.ok(Math.abs(value/factor-cm)<=.01);
  }
});
test('las etiquetas de tablero y todas las piezas cambian; sierra permanece en mm',()=>{
  const s=setup('ft');s.api.updateLabels();
  assert.equal(s.nodes.unidad_ancho.textContent,'(ft)');assert.equal(s.nodes.unidad_alto.textContent,'(ft)');
  assert.ok(s.labels.every(n=>n.textContent==='(ft)'));assert.equal(s.kerf.textContent,'(mm)');
  s.labels.push({});s.api.updateLabels();assert.equal(s.labels[2].textContent,'(ft)');
});
test('en Inicio se presentan medidas de material sin cambiar selección ni precio',()=>{
  const s=setup();s.api.updateLabels({materialOptions:true});
  assert.equal(s.options[1].textContent,'OSB (1.22×2.44 m)');
  assert.equal(s.options[0].textContent,'Elegir material');assert.equal(s.nodes.material_select.value,'1');
});
test('Editar conserva las etiquetas del selector de material si no solicita actualizarlas',()=>{
  const s=setup();s.api.updateLabels();assert.equal(s.options[1].textContent,'OSB guardado');
});
test('tolera formularios sin campos opcionales',()=>{
  const s=setup();delete s.nodes.material_select;s.api.updateLabels({materialOptions:true});
  delete s.nodes.unidad_medida_selector;assert.doesNotThrow(()=>s.api.updateLabels());
});
