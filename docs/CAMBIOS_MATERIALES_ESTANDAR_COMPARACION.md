# Materiales estándar y visibilidad de gráficos — 31/10/2026

## Problema
Elegir una medida habitual OSB/MDF/etc. completaba dimensiones pero solo conservaba el material si existía una ficha de biblioteca coincidente. La comparación mostraba «Sin especificar». Los gráficos quedaban debajo de la tabla y el gráfico de costos se omitía sin una explicación cercana.

## Cambios
- Catálogo compartido de medidas habituales. Se guarda la clave elegida explícitamente en el JSON existente `Optimizacion.resultado_extra.medida_habitual`; no se crean materiales ni migraciones.
- Campo oculto validado por Django: clave del catálogo y dimensiones físicas coincidentes (tolerancia de 0,01 cm), también cuando se trabaja en metros u otras unidades. Una selección desactualizada se descarta, nunca cambia el cálculo ni fuerza medidas.
- Se conserva la selección al editar/duplicar y al refrescar la persistencia de un resultado. Un cambio explícito a medida personalizada elimina la referencia.
- El selector ya no adivina OSB a partir de 122 × 244. Cambiar manualmente dimensiones incompatibles elimina la selección estándar; seleccionar una ficha de biblioteca da prioridad a esa ficha.
- La comparación distingue ficha de biblioteca, selección estándar y tablero habitual/personalizado cuyo tipo no se registró. Los registros antiguos no permiten recuperar con certeza un tipo que nunca se guardó: no se inventa por dimensiones compartidas.
- Cambiar de estándar limpia una ficha anterior que no coincide, evitando mostrar su material/precio como si correspondieran. No se inventan precios para los estándares. Un precio cero coincidente se conserva.
- Gráficos en una tarjeta explícita junto al resumen, antes de la tabla; enlace «Ver gráficos» en la cabecera. Material se muestra sin necesitar precio. Si falta precio en algún plan, se explica por qué no aparece el gráfico de costos.

## Verificación
Pruebas de selección/persistencia sin biblioteca, mantenimiento al refrescar/editar/duplicar, descarte al cambiar dimensiones, prioridad de biblioteca, unidades, eliminación explícita, flujo de creación y gráfico de material sin precio. El algoritmo y sus dimensiones no se modifican.

Sin commit, push ni despliegue. En registros anteriores se informa la procedencia disponible; para registrar el tipo se debe elegirlo y guardar nuevamente el corte.

Validación final: **240 pruebas Django aprobadas**, comprobación de sintaxis de `medidas-pred.js` y `git diff --check` sin errores. En navegador local se verificaron la selección explícita OSB, su eliminación al modificar dimensiones, la selección de biblioteca coincidente y los gráficos de material/costo con dos selecciones estándar.
