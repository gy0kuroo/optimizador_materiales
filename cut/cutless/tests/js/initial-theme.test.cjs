const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const html = fs.readFileSync(path.join(__dirname, '../../templates/cutless/base.html'), 'utf8');
const script = html.match(/<script>([\s\S]*?)<\/script>/)[1];
function initialTheme(profile, saved, systemDark, blocked = false, profileSize = '', savedSize = null, manual = {}) {
  const attrs = {};
  const style = {};
  const source = script.replace(/const profileTheme = ".*";/, `const profileTheme = ${JSON.stringify(profile)};`)
    .replace(/const user = ".*";/, `const user = ${JSON.stringify(profile ? '8' : '')};`)
    .replace(/let fontSize = ".*";/, `let fontSize = ${JSON.stringify(profileSize)};`);
  vm.runInNewContext(source, {
    document: {documentElement: {style, setAttribute: (key, value) => {attrs[key] = value;}}},
    localStorage: {getItem(key) {if (blocked) throw new Error('Bloqueado'); return key === 'fontSize' ? savedSize : saved;}},
    sessionStorage: {
      getItem(key) { if (blocked) throw new Error('Bloqueado'); return manual[key]; },
      removeItem(key) { delete manual[key]; },
    },
    window: {matchMedia: () => ({matches: systemDark}), addEventListener() {}},
  });
  return {...attrs, fontSize: style.fontSize};
}
test('el cambio rápido depende de la cuenta y del tema guardado antes del primer pintado', () => {
  const manual = {'cutless:tema:8': 'auto:dark', 'cutless:tema:9': 'light:dark'};
  assert.equal(initialTheme('auto', 'light', false, false, '', null, manual)['data-theme'], 'dark');
  assert.equal(initialTheme('auto', 'light', false, true, '', null, manual)['data-theme-choice'], 'auto');
  assert.equal(initialTheme('', 'light', false, false, '', null, manual)['data-theme'], 'light');
  assert.equal(initialTheme('light', 'dark', true, false, '', null, manual)['data-theme'], 'light');
  assert.deepEqual(manual, {'cutless:tema:9': 'light:dark'});
});
test('el tema del perfil prevalece desde el primer pintado', () => {
  assert.equal(initialTheme('dark', 'light', false)['data-theme'], 'dark');
  assert.equal(initialTheme('light', 'dark', true)['data-theme'], 'light');
  assert.equal(initialTheme('auto', 'light', true)['data-theme'], 'dark');
});
test('sin perfil usa preferencia guardada o sistema, incluso sin almacenamiento', () => {
  assert.equal(initialTheme('', 'dark', false)['data-theme'], 'dark');
  assert.equal(initialTheme('', null, true)['data-theme'], 'dark');
  assert.equal(initialTheme('', null, false, true)['data-theme'], 'light');
  assert.equal(initialTheme('', 'invalido', true)['data-theme'], 'dark');
});

test('aplica tamaño antes del contenido y respeta perfil o preferencia local', () => {
  assert.equal(initialTheme('dark', null, false, false, 'large', 'small').fontSize, '18px');
  assert.equal(initialTheme('', null, false, false, '', 'xlarge').fontSize, '20px');
  assert.equal(initialTheme('', null, false, true).fontSize, '16px');
  assert.equal(initialTheme('', null, false, false, '', 'invalido').fontSize, '16px');
});
