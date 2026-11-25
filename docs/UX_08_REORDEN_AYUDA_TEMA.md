# UX-08 · Orden de Cuenta y Ayuda y cambio rápido de tema

La implementación parte de `d693ba0e491daebefdeab2ba8712bf9e702b3e3d`, que incluye NOTI-01. Cuenta aparece antes de Ayuda en el menú lateral y en la navegación móvil. Conserva sus enlaces, permisos y comportamiento como grupo expandible. El orden del marcado coincide con el orden visual y de teclado. La Ayuda de Inicio usa el título del contenido principal como ancla para su primer paso. El encabezado también contiene el título de Notificaciones, que puede estar oculto.

## Cambio rápido de tema

El botón aparece en el encabezado compartido de los paneles autenticados, fuera del menú plegable. El icono y el nombre accesible indican la acción disponible. La luna cambia a oscuro y el sol cambia a claro. El control tiene foco visible y un área táctil de al menos 44 × 44 px. En el lateral las acciones pueden ocupar una segunda línea y en pantallas menores de 360 px se usa una marca más compacta.

El botón aplica el cambio en `theme.js` y lo recuerda en la pestaña mediante `sessionStorage`, con alcance por cuenta y asociado al valor guardado en el perfil. El script inicial aplica esa selección antes de los estilos y al restaurar la página desde la caché de navegación. La preferencia guardada en el perfil, incluido Automático, sigue disponible en **Cuenta → Mi perfil**. Elegir un valor en ese selector vuelve a la previsualización del formulario. Confirmar el guardado elimina el ajuste temporal y usa el valor guardado en la siguiente carga. El botón rápido no cambia el valor del formulario, el tema local de las páginas públicas ni los datos de la cuenta.

El tema temporal de la pestaña no se sincroniza entre dispositivos. Si el navegador bloquea `sessionStorage`, el botón cambia el tema de la página actual. Sin JavaScript, se oculta el botón y se conserva la configuración por formulario. El asistente de personalización inicial mantiene su encabezado y su selector propio de apariencia. UX-08 no requiere migraciones ni cambios en el modelo de preferencias.

## Archivos modificados

| Área | Archivos |
| --- | --- |
| Encabezado, orden y Ayuda | `cut/cutless/templates/cutless/base.html`, `cut/cutless/templates/cutless/includes/authenticated-navigation.html`, `cut/cutless/templates/cutless/includes/tutorial-scripts.html` |
| Tema, iconos y estilos | `cut/cutless/static/cutless/js/theme.js`, `cut/cutless/static/cutless/button-icons.svg`, `cut/cutless/static/cutless/css/reforma-visual.css`, `cut/cutless/static/cutless/css/sidebar-navigation.css` |
| Pruebas | `cut/cutless/tests/test_initial_presentation.py`, `cut/cutless/tests/js/initial-theme.test.cjs`, `cut/cutless/tests/browser/reorden-ayuda-tema.cjs` |
| Documentación | `docs/UX_08_REORDEN_AYUDA_TEMA.md` |

## Verificación

Desde `cut/` con `CUTLESS_ENV=development` y `CUTLESS_DB_*` apuntando a bases desechables locales, se ejecutaron `python manage.py test --noinput`, `python manage.py check` y `python manage.py makemigrations --check --dry-run`. Desde la raíz se ejecutaron `git ls-files -z '*.test.cjs' '*.test.mjs' | xargs -0 node --test` y `git diff --check`.

Los recorridos de Chromium reutilizan el fixture sintético de NOTI-01 en SQLite. El procedimiento y las variables de Playwright se encuentran en [NOTI-01](NOTI_01_CAMPANA_ALERTAS.md). Desde `cut/` ejecutar `node cutless/tests/browser/reorden-ayuda-tema.cjs` en una copia fresca del fixture. El recorrido usa las copias locales de Bootstrap e Intro.js que ya emplea la interfaz.

| Verificación | Aprobadas | Fallidas | Omitidas |
| --- | ---: | ---: | ---: |
| Django completo con PostgreSQL 16 local | 576 | 0 | 0 |
| Django completo con SQLite local | 564 | 0 | 12 |
| JavaScript | 83 | 0 | 0 |
| Playwright con Chromium 156 | 2 recorridos | 0 | 0 |

Las doce omisiones de SQLite requieren `SELECT FOR UPDATE` y pasaron en PostgreSQL. Las 16 pruebas de presentación y alertas se repitieron en ambos motores. `check`, `makemigrations --check --dry-run` y `git diff --check` pasaron.

El recorrido de UX-08 verificó 320, 390, 768 y 1440 px en claro y oscuro, el orden y foco de los controles, el cierre del menú móvil al abrir Ayuda, el acceso al perfil, la persistencia al recargar y navegar, y el guardado de Automático. El recorrido de NOTI-01 verificó el encabezado, la campana, sus filtros y la página sin JavaScript. El primer recorrido preliminar detectó el ancla de Ayuda dentro del panel oculto. Las siguientes ejecuciones ajustaron la espera del evento de cambio del sistema y la confirmación propia del formulario antes de comprobar el POST. Firefox, WebKit y dispositivos físicos quedaron fuera de esta verificación.

## Evidencias

Las capturas se guardaron fuera de Git con datos sintéticos. `ux08-320-light.png` muestra el encabezado compacto con foco, `ux08-390-menu.png` muestra Cuenta y Ayuda en la navegación móvil, y `ux08-1440-dark.png` y `ux08-1440-light.png` muestran el lateral en ambos temas. También se generaron `ux08-390-dark.png`, `ux08-768-dark.png`, `ux08-320-menu.png` y `ux08-768-menu.png`.
