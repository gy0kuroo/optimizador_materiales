# Limpieza de código — primera etapa

Fecha: 1 de noviembre de 2026.

## Objetivo
Retirar redundancias confirmadas para facilitar el mantenimiento y la explicación del código, conservando las funciones y el diseño actuales.

## Cambios
- `cutless/views/optimization.py`: eliminar el procesamiento POST heredado de `resultado_view`. La única ruta publicada exige un identificador y retornaba antes de esa rama. La vista ahora recibe `pk` obligatorio y muestra el resultado guardado del propietario. Crear se procesa en `index`; actualizar en `editar_optimizacion`; ambos redirigen al resultado.
- Retirar las tres asignaciones sin consumidores de `imagen_principal` (una pertenecía a la rama heredada) y un comentario de vista previa desfasado.
- `cutless/static/cutless/js/theme.js`: eliminar una segunda lectura de la misma preferencia del perfil. Se conserva la prioridad perfil → preferencia local → automático.
- Retirar nueve imports sin uso local y sin consumidores encontrados en vistas de usuarios, formularios de usuarios/presupuestos/plantillas, análisis y exportación PDF. No eliminar clases: `PerfilForm`, por ejemplo, sigue siendo la base de los formularios especializados.

## Verificación
- **250 pruebas Django aprobadas**, sobre una base de pruebas aislada; incluye autenticación, permisos, optimización, recarga, precisión dimensional y exportaciones.
- **3 pruebas JavaScript de tema/tamaño inicial aprobadas**, más comprobación de sintaxis del script de tema.
- Sintaxis Python y `git diff --check` correctos.
- Sin migraciones, dependencias nuevas, cambios de diseño ni cambios en el algoritmo. No se conectó a Supabase ni se utilizaron datos reales para las pruebas.

## Pendiente para etapas siguientes
- Revisar la extracción de la política específica de materiales de cada pantalla si aporta claridad; la gestión de filas y las utilidades de presentación ya están centralizadas.
- Consolidar las reglas CSS por componente, verificando su apariencia por secciones.
- Dividir `base.html` en parciales y scripts más pequeños.
- Confirmar uso dinámico de los recursos sin referencias encontradas antes de retirarlos.

Se conservan las migraciones, las fachadas de compatibilidad y la lectura de archivos históricos. Esta primera etapa no elimina archivos basándose únicamente en su antigüedad.

## Segunda etapa: gestión compartida de piezas
- `piece-formset.js` centraliza inicialización, añadido, eliminación, numeración, actualización de TOTAL_FORMS y visibilidad de eliminar. `reindex` sigue manteniendo asociados nombres, IDs, etiquetas y referencias accesibles.
- Inicio y Editar llaman a `CutlessPieceForms.init` en lugar de repetir los controladores. Inicializar el mismo contenedor dos veces no añade eventos duplicados.
- Se conserva al menos una fila; las filas nuevas vacían nombre y medidas, dejan cantidad en uno y retiran los mensajes de error clonados. Las filas existentes conservan sus valores.
- El límite y su mensaje son comunes: veinte tipos de pieza, no veinte unidades. Las conversiones, selección de materiales y controles específicos de costos mantienen su lógica existente.
- Se elimina también una lectura sin uso de `addButton.onclick` de cada plantilla.
- Verificación: **6 pruebas JavaScript de piezas y 7 pruebas Django dirigidas aprobadas**, además de sintaxis JS y `git diff --check`. Las 250 pruebas Django generales de la primera etapa ya estaban aprobadas antes de esta extracción.
- No hay cambios de diseño, cálculo, base de datos, dependencias ni exportaciones.

## Tercera etapa: unidades y presentación de materiales
- `cutless/static/cutless/js/units.js` comparte conversión desde centímetros con seis decimales, símbolos, etiquetas de tablero/piezas y presentación de las medidas de materiales.
- Inicio y Editar consumen el módulo compartido. La sierra conserva siempre la etiqueta en milímetros.
- Se preserva una diferencia funcional existente: Inicio puede completar precio y medidas al elegir material, respetando sus controles de entrada manual; Editar solo actualiza el precio al cambiar material. No se unifican esas políticas ni se sobrescriben los datos existentes de edición.
- Las etiquetas del selector de materiales solo se regeneran en Inicio, como antes. La selección y el precio no se modifican al actualizar sus textos.
- Se mantienen los eventos y tiempos de inicialización existentes; no se cambian la lógica de medidas habituales ni la validación dimensional del servidor.
- Verificación acumulada: **250 pruebas Django y 48 JavaScript aprobadas** (nueve archivos de pruebas JavaScript).
- Seis pruebas nuevas cubren conversiones conocidas, comparación exacta con la fórmula anterior para 5.000 conversiones, tolerancia de 0,01 cm, etiquetas de nuevas piezas, sierra en mm, presentación de materiales y campos opcionales ausentes.
- Sintaxis JS, referencias de las dos plantillas y `git diff --check` correctos. Sin cambios visuales intencionados, migraciones ni dependencias nuevas.

Las pruebas reducen el riesgo de regresión, pero no sustituyen una comprobación de los flujos reales después del despliegue. Este bloque todavía no está publicado.

## Cuarta etapa: CSS de resultados
- Retirar reglas de la disposición antigua `.board-layout`, métricas `.board-metrics` y tarjetas `.metric-card`/`.metric-value` limitadas a resultados, sin consumidores encontrados en plantillas o JavaScript actuales. Las tarjetas estadísticas de otras pantallas se conservan.
- Concentrar los estilos de acciones finales y resumen plegable en `resultado.css`. Se eliminan las alineaciones antiguas de centro/izquierda de las hojas generales, conservando la alineación derecha y el apilado móvil efectivos.
- Trasladar también el ancho móvil de los botones al archivo propietario, preservando flex-wrap y separación de 12 px heredados de la hoja anterior.
- Versionar las referencias de las hojas editadas para evitar mezclar CSS antiguo y nuevo en el navegador.
- Comparación de navegador antes/después, con datos sintéticos en modo oscuro: diez componentes (acciones, botones, plegable, columnas, tablero y costos), diecisiete propiedades por componente, a 1440 y 390 px. **Cero diferencias en las propiedades comparadas**. Esta comprobación no equivale a una comparación de todos los estados de toda la aplicación.
- Seis pruebas Django dirigidas a resultado y recarga aprobadas; `git diff --check` correcto. La batería general de 250 Django y 48 JavaScript ya estaba aprobada en la etapa anterior; esta etapa solo modifica CSS y versiones de recursos.
- No cambia HTML de los componentes, datos, eventos, cálculos ni exportaciones. No se conectó con Supabase.
- Evidencia local fuera del repositorio: `comparacion-limpieza-css.json` y `resultado-limpieza-css.png`, en el directorio de visualizaciones de la sesión.

Pendiente: continuar por componentes con otras reglas del visor y las capas generales. No se ha intentado consolidar todo el CSS de una sola vez.

## Quinta etapa: estilos del visor
- Retirar del resultado las columnas antiguas del visor, el flex inicial del área de dibujo, el fondo blanco fijo y las alturas/márgenes móviles que siempre eran sustituidos por `board-landscape.css`.
- El viewport histórico también deja de declarar flex y fondo blanco ya anulados por el diseño horizontal y el tema.
- El padding y fondo efectivos del cuerpo del visor de resultados pasan de `reforma-visual.css` a `resultado.css`, con la especificidad necesaria para conservar el comportamiento actual. Las columnas, alturas y disposición móvil efectivas siguen en `board-landscape.css`.
- Se conserva el fallback de imágenes antiguas, las rutas, el SVG, el zoom y todos los controles.
- Comparación de navegador en modo oscuro, a 1440 y 390 px: ambos visores conservan las propiedades medidas. La primera medición de resultados mostró diferencias transitorias de tamaño; al repetir con las hojas previas y actuales, el mismo tablero y Ajustar tablero, la comparación controlada no mostró diferencias. El historial coincidió en la comparación inicial.
- Comprobación funcional en ambos visores: pasar al tablero 2 de 3, ampliar a 125 % y volver a Ajustar tablero; sin errores en consola.
- **7 pruebas Django del visor/carga y 48 pruebas JavaScript aprobadas**. No se añaden pruebas que solo reproduzcan reglas CSS; se utiliza comparación en navegador y las regresiones funcionales existentes.
- Evidencia local fuera del repositorio: `comparacion-visores-css.json` y `visor-limpieza-css.png`.
- Solo CSS y versiones de recursos; sin cambios de datos, algoritmo, exportaciones ni migraciones. Sin commit ni publicación.

## Sexta etapa: separar el tutorial de la plantilla base
- `base.html` conserva la estructura de la página, las condiciones de autenticación y el orden de carga. Se extraen el bloque de scripts de ayuda a `includes/tutorial-scripts.html` y el diálogo de bienvenida a `includes/welcome-dialog.html`.
- La plantilla base pasa de aproximadamente 1.046 líneas a unas 250. El tutorial no se reescribe ni se traslada a un JavaScript externo: conserva las variables y URLs que genera Django.
- Comparación de renderizado antes/después para visitante, usuario nuevo, tutorial completado y tutorial oculto: mismos nodos HTML/atributos/contenido y mismos textos de scripts. Solo varía el espacio de indentación entre elementos.
- Tres regresiones adicionales verifican las condiciones de inclusión, una sola definición del controlador/diálogo y la disponibilidad de ayuda manual después de completar el tutorial.
- **253 pruebas Django y 48 JavaScript aprobadas** sobre entornos aislados. `git diff --check` correcto.
- Sin cambios visuales, de eventos, red, autenticación, algoritmo o base de datos. Sin commit ni publicación.

## Séptima etapa: navegación autenticada y controles de lupa
- Extraer las opciones del usuario a `includes/authenticated-navigation.html` y la herramienta de ampliación a `includes/magnifier-controls.html`.
- `base.html` conserva la estructura del navbar, la resolución de sección activa, las condiciones de autenticación y el bloque heredable `show_auth_buttons`. No se traslada este bloque a un include: hacerlo impediría que login y recuperación de contraseña lo sobrescriban como hasta ahora.
- Cada parcial carga explícitamente sus bibliotecas de etiquetas. Se mantienen IDs, URLs, condiciones de herramientas opcionales/administración, atributos accesibles y orden de scripts.
- La plantilla base queda en 201 líneas.
- Comparación antes/después: mismos nodos, atributos, contenido y scripts para visitante, usuario con menú limitado, menú completo con Materiales activo y administrador.
- Tres regresiones adicionales cubren personalización de botones de acceso desde una plantilla hija, menú básico/opcional, visibilidad única de la lupa, grupo activo y enlace de administración.
- Validación acumulada: **256 pruebas Django y 48 JavaScript aprobadas**, más `git diff --check`. Las pruebas se ejecutan con base aislada.
- Sin cambios de diseño, permisos efectivos, eventos, cálculos, datos ni migraciones. Sin commit ni publicación.

## Octava etapa: recursos sin consumidores y helper antiguo de PDF
- Retirar `pdf_path_para_template` y su exportación pública, junto con `_ruta_pdf_en_disco`, `_normalizar_ruta_absoluta` y `_media_root`: solo formaban una cadena interna sin consumidores encontrados en el proyecto. Retirar también sus imports exclusivos `os` y `settings`.
- La descarga actual sigue utilizando `respuesta_pdf_optimizacion` y la generación en memoria. Se conservan los campos históricos del modelo, el acceso privado a archivos existentes y la lectura de imágenes guardadas.
- Retirar cuatro archivos versionados sin referencias en el código de ejecución actual:
  - `usuarios/static/usuarios/css/perfil.css` (242 líneas).
  - `usuarios/static/usuarios/css/registro.css` (137 líneas).
  - `cutless/static/cutless/css/historial_costos.css` (107 líneas).
  - `cutless/templates/cutless/partials/page_header.html` (11 líneas).
- La documentación visual antigua que menciona `perfil.css` describe una etapa anterior; la búsqueda de consumidores actuales no encontró pantallas que lo carguen. Las hojas actuales de perfil, registro y análisis se mantienen.
- Comprobación de las 72 rutas estáticas literales presentes en las plantillas: todas resuelven a archivos existentes después de la retirada.
- **256 pruebas Django y 48 JavaScript aprobadas**, incluidas las regresiones de exportaciones, propiedad de los datos y lectura de resultados guardados. `git diff --check` correcto.
- No se borran PDFs, imágenes, optimizaciones, datos ni migraciones. Los archivos retirados son código versionado recuperable desde Git. Sin commit ni publicación.

## Revisión final previa a publicación
- Alcance identificado: **33 archivos** del bloque de limpieza, incluidos módulos nuevos, parciales, pruebas y este documento. README, CAMBIOS_AREAS y los materiales de otras tareas quedan fuera.
- **256 pruebas Django y 48 JavaScript aprobadas** en la revisión final; sin incidencias del sistema Django.
- Sintaxis de 115 archivos Python y compilación de 67 plantillas correctas. Includes y extends literales resuelven; 72 recursos estáticos literales existentes. Diff sin errores de formato.
- Búsqueda de patrones de credenciales en las líneas añadidas y archivos nuevos del bloque: sin coincidencias; no se incluyen bases locales ni archivos de entorno.
- Navegador con datos sintéticos aislados: añadir filas en metros, eliminar una fila intermedia y añadir otra conserva valores e IDs únicos; las etiquetas apuntan al campo de su propia fila.
- Selección de material en Inicio: 122 × 244 cm se presenta como 1,22 × 2,44 m y completa el precio esperado. En Editar, elegir material conserva las medidas guardadas y solo cambia el precio.
- Editar con veinte tipos mantiene el límite y muestra el diálogo correspondiente al intentar añadir otro. Sin errores JavaScript en consola.
- Se mantienen las comprobaciones visuales previas del resultado y los visores, y la equivalencia de HTML/scripts de la extracción de parciales.
- No se encontraron bloqueos para publicar este bloque. Validación local; no se desplegó ni se probó contra Render/Supabase en esta revisión. No se realizó git add, commit o push.
