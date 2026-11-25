const assert = require('node:assert/strict');
const path = require('node:path');
const { chromium } = require('playwright');
const { contexto, fixture, origen } = require('./estadisticas-descargas-helpers.cjs');

const intro = process.env.CUTLESS_TEST_INTRO_DIR;
const evidencia = process.env.CUTLESS_TEST_EVIDENCE;
const campana = page => page.locator('[data-alertas-boton]');
const tema = page => page.locator('#theme-toggle');
const menu = page => page.getByRole('button', { name: 'Abrir navegación' });

async function comprobarTema(page, actual) {
  const icono = actual === 'dark' ? 'sun' : 'moon';
  const accion = actual === 'dark' ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro';
  await page.locator(`html[data-theme="${actual}"]`).waitFor({ state: 'attached' });
  assert.equal(await tema(page).getAttribute('aria-label'), accion);
  assert.equal(await tema(page).getAttribute('data-icon'), icono);
  await tema(page).locator(`use[href$="#${icono}"]`).waitFor({ state: 'attached' });
}

async function comprobarEncabezado(page) {
  const medidas = await page.locator('.app-header-row').evaluate(row => {
    const caja = selector => row.querySelector(selector).getBoundingClientRect();
    const marca = [caja('.brand-symbol'), caja('.brand-wordmark')];
    const controles = [caja('#theme-toggle'), caja('[data-alertas-boton]'), caja('.navbar-toggler')]
      .filter(rect => rect.width);
    const solapados = (a, b) => a.right > b.left && b.right + 5 > a.left && a.bottom > b.top && b.bottom > a.top;
    return {
      fuera: controles.some(rect => rect.left < 0 || rect.right > innerWidth || rect.width < 44 || rect.height < 44),
      cruces: controles.some((rect, i) => marca.some(parte => solapados(rect, parte)) ||
        controles.slice(i + 1).some(otro => solapados(rect, otro))),
      scroll: document.documentElement.scrollWidth - innerWidth,
    };
  });
  assert.deepEqual(medidas, { fuera: false, cruces: false, scroll: 0 });
}

async function captura(page, ancho, variante) {
  if (evidencia) await page.screenshot({ path: path.join(evidencia, `ux08-${ancho}-${variante}.png`) });
}

async function confirmarPreferencias(page) {
  const destino = page.url();
  await page.getByRole('button', { name: 'Guardar preferencias', exact: true }).press('Enter');
  const confirmar = page.getByRole('dialog', { name: '¿Guardar cambios?' });
  const [respuesta] = await Promise.all([
    page.waitForResponse(r => r.url() === destino && r.request().method() === 'POST'),
    page.waitForResponse(r => r.url() === destino && r.request().method() === 'GET' && r.status() === 200),
    confirmar.getByRole('button', { name: 'Sí, guardar', exact: true }).press('Enter'),
  ]);
  assert.equal(respuesta.status(), 302);
  await page.waitForLoadState('load');
  await tema(page).waitFor();
}

async function probarAncho(browser, ancho, inicial, guardado) {
  const context = await contexto(browser, origen, {
    viewport: { width: ancho, height: 900 }, colorScheme: inicial, reducedMotion: 'reduce',
  });
  try {
    await context.route('https://cdn.jsdelivr.net/npm/intro.js@7.2.0/minified/*', ruta =>
      ruta.fulfill({ path: path.join(intro, path.basename(new URL(ruta.request().url()).pathname)) }));
    await context.addCookies([{ name: 'sessionid', value: fixture.sesiones[ancho], url: origen }]);
    const page = await context.newPage();
    await page.goto(origen + fixture.inicio);
    await tema(page).waitFor();
    await campana(page).waitFor();
    await comprobarTema(page, inicial);
    await comprobarEncabezado(page);
    if (ancho === 1440) await captura(page, ancho, inicial);
    const esMovil = ancho < 1200;
    if (esMovil) assert.equal(await page.locator('#nav-cuenta').isVisible(), false);
    let posts = 0;
    page.on('request', request => {
      if (request.method() === 'POST' && new URL(request.url()).pathname !== '/usuarios/actividad/') posts++;
    });

    const cambio = inicial === 'light' ? 'dark' : 'light';
    await page.locator('.navbar-brand').focus();
    await page.keyboard.press('Tab');
    assert.equal(await tema(page).evaluate(e => e === document.activeElement && e.matches(':focus-visible') &&
      getComputedStyle(e).outlineStyle === 'solid'), true);
    await page.keyboard.press('Space');
    await comprobarTema(page, cambio);
    await comprobarEncabezado(page);
    await captura(page, ancho, cambio);
    await page.reload();
    await tema(page).waitFor();
    await comprobarTema(page, cambio);
    assert.equal(await page.evaluate(() => localStorage.getItem('theme')), guardado);
    assert.equal(posts, 0);
    // Un cambio de apariencia del dispositivo respeta la elección manual.
    await page.emulateMedia({ colorScheme: cambio });
    await page.emulateMedia({ colorScheme: inicial });
    await comprobarTema(page, cambio);

    if (esMovil) await menu(page).press('Enter');
    const cuenta = page.locator('#nav-cuenta');
    const ayuda = page.getByRole('button', { name: 'Ayuda', exact: true });
    await cuenta.waitFor();
    const cajaCuenta = await cuenta.boundingBox();
    const cajaAyuda = await ayuda.boundingBox();
    assert.ok(cajaAyuda.y >= cajaCuenta.y + cajaCuenta.height);
    await cuenta.focus();
    await page.keyboard.press('Tab');
    assert.equal(await ayuda.evaluate(e => e === document.activeElement), true);
    await page.keyboard.press('Enter');
    const tutorial = page.getByRole('dialog', { name: '¡Bienvenido a CutLess!' });
    await tutorial.waitFor();
    await page.keyboard.press('Escape');
    await tutorial.waitFor({ state: 'hidden' });
    await page.waitForFunction(() => !document.body.classList.contains('tutorial-running'));
    if (esMovil) {
      assert.equal(await cuenta.isVisible(), false);
      await menu(page).press('Enter');
      await cuenta.waitFor();
      await captura(page, ancho, 'menu');
    } else {
      assert.equal(await ayuda.evaluate(e => e === document.activeElement), true);
    }
    await cuenta.press('Enter');
    await page.getByRole('link', { name: 'Mi perfil', exact: true }).press('Enter');
    const preferencia = page.locator('select[name="tema_preferido"]');
    await preferencia.waitFor();
    assert.equal(await preferencia.inputValue(), guardado);
    await comprobarTema(page, cambio);
    await comprobarEncabezado(page);
    await campana(page).press('Enter');
    await page.getByRole('heading', { name: 'Notificaciones', exact: true }).waitFor();
    await campana(page).press('Escape');
    await tema(page).press('Enter');
    await comprobarTema(page, inicial);
    assert.equal(await preferencia.inputValue(), guardado);
    if (ancho === 390) {
      await tema(page).press('Enter');
      await page.getByRole('button', { name: 'Guardar preferencias', exact: true }).press('Enter');
      await page.getByRole('dialog', { name: '¿Guardar cambios?' })
        .getByRole('button', { name: 'Cancelar', exact: true }).press('Enter');
      await page.reload();
      await tema(page).waitFor();
      await comprobarTema(page, cambio);
      await confirmarPreferencias(page);
      await comprobarTema(page, inicial);
    }

    // El selector sigue pudiendo volver a Automático y seguir al sistema.
    await preferencia.selectOption(guardado === 'auto' ? 'dark' : 'auto');
    if (guardado === 'auto') await preferencia.selectOption('auto');
    await page.emulateMedia({ colorScheme: 'dark' });
    await comprobarTema(page, 'dark');
    await page.emulateMedia({ colorScheme: 'light' });
    await comprobarTema(page, 'light');
    if (ancho === 390) {
      await confirmarPreferencias(page);
      assert.equal(await preferencia.inputValue(), 'auto');
      await page.emulateMedia({ colorScheme: 'dark' });
      await comprobarTema(page, 'dark');
    }
    console.log(`${ancho} px · navegación, Ayuda, tema, persistencia y teclado aprobados`);
  } finally {
    await context.close();
  }
}

async function main() {
  assert.ok(intro, 'Indica CUTLESS_TEST_INTRO_DIR con los archivos minificados locales de Intro.js 7.2.0.');
  const browser = await chromium.launch({ executablePath: process.env.CUTLESS_TEST_CHROMIUM || undefined });
  try {
    for (const [ancho, tema, guardado] of [[320, 'dark', 'auto'], [390, 'light', 'light'],
      [768, 'light', 'auto'], [1440, 'dark', 'dark']]) await probarAncho(browser, ancho, tema, guardado);
  } finally {
    await browser.close();
  }
}

main().catch(error => { console.error(error); process.exitCode = 1; });
