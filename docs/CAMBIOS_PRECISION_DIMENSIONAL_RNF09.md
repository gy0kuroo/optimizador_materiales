# Corrección de precisión dimensional — RNF-09

Fecha: 25 de octubre de 2026. Entorno local: Python 3.13.12, Django 5.2.8.

## Problemas corregidos

- Las conversiones redondeaban a dos decimales independientemente de la unidad. Por ejemplo, 60,9 cm se mostraban como 0,61 m y al convertirlos de vuelta resultaban 61 cm. Ahora las conversiones conservan seis decimales; se eliminaron los redondeos adicionales en los formularios de edición, medidas habituales y selección de materiales.
- Los campos de dimensiones permiten introducir los decimales necesarios (`step="any"`), manteniendo las validaciones de valor existentes. No se modificaron los pasos ni el formato de los precios y del ancho de sierra.
- Al editar, las piezas guardadas en metros o pies se convertían nuevamente como si estuvieran en centímetros. Ahora se conserva su unidad original; únicamente se convierte el tablero, que se almacena en centímetros. Se corrigió también esa conversión duplicada en el detalle de piezas del PDF de presupuesto.
- Se evita reducir las medidas lineales a dos decimales en el dibujo web y su tabla, y se retiraron redondeos adicionales de medidas en exportaciones y advertencias. Las áreas, porcentajes y precios mantienen su formato.
- La reserva del ancho de sierra podía exceder el borde exterior y provocar que una pieza válida se omitiera. Ahora esa reserva termina en el perímetro del tablero. No se reducen las dimensiones de las piezas ni la separación entre ellas. El recorte de la reserva solo se aplica al perímetro exterior, no al límite de un hueco interior.

## Validación automatizada

Se añadió `cut/cutless/tests/test_precision_rnf09.py`, con siete pruebas de regresión:

1. Conversión de ida y vuelta de 206 medidas por unidad: cm, mm, m, pulgadas y pies, incluyendo el alias `pulgadas` (1.236 comprobaciones). Tolerancia máxima admitida: 0,01 cm.
2. Conversión de sierra: 3 mm = 0,3 cm. Los guardados reales también comprueban que este valor llegue a la optimización.
3. Caso de dos piezas de 60,9 × 130 cm: dos tableros con sierra de 3 mm; un tablero con sierra de 0 mm. Control de dos piezas de 60,85 × 130 cm: un tablero con sierra de 3 mm.
4. Piezas cercanas a los bordes: 121,9 × 130; 122 × 244; 50 × 243,9; 121,99 × 243,99 cm, con y sin rotación. Todas se colocan sin omisiones.
5. Quinientos escenarios pseudoaleatorios reproducibles (semilla 903), alternando rotación, con dimensiones de tres decimales y distintas cantidades; además del caso de 50 piezas del RNF-03. Se comprueban cantidades y dimensiones originales, orientación, límites y separación de sierra entre todos los pares de piezas de cada tablero.
6. Carga de edición y duplicación en cinco unidades, conservando tablero y piezas.
7. POST real de edición, persistencia y nueva carga en metros y pies, con generación de archivos en una carpeta temporal. Se conservan las dimensiones y los dos tableros del caso crítico.

### Resultados

Suite completa: **169 pruebas aprobadas, 0 fallos**. Duración de la última ejecución: 12,322 segundos. Este tiempo corresponde a la suite, no a una medición de rendimiento del RNF-03.

| Unidad | Mayor error de ida y vuelta observado (cm) | Límite RNF-09 |
| --- | ---: | ---: |
| cm | 0,000000499 | 0,01 |
| mm | 0,000000549 | 0,01 |
| m | 0,000049743 | 0,01 |
| in | 0,000001563 | 0,01 |
| ft | 0,000015474 | 0,01 |
| pulgadas (alias) | 0,000001561 | 0,01 |

No se detectaron superposiciones, excesos de los límites ni separaciones inferiores al ancho de sierra en los escenarios comprobados. Los cálculos geométricos se contrastan mediante comprobaciones independientes de coordenadas, sin usar los rectángulos libres del motor como referencia de validez.

Además: plantillas compiladas correctamente, comprobación sintáctica del JavaScript de medidas habituales aprobada, `makemigrations --check --dry-run` sin cambios y `git diff --check -- cut/cutless` sin incidencias.

## Ejecución y aislamiento

La suite se ejecutó mediante `call_command('test', 'cutless', 'usuarios', verbosity=1)`, con `DJANGO_SETTINGS_MODULE=cutless_project.settings`, `cut` en `sys.path` y `settings.MEDIA_ROOT` apuntando a una carpeta creada con `tempfile.mkdtemp`. Django utilizó su base de datos de prueba. No se usaron la base de datos de trabajo ni sus archivos multimedia para guardar los resultados de estas pruebas.

Para ejecutar únicamente estas regresiones, usar el mismo aislamiento y llamar a `call_command('test', 'cutless.tests.test_precision_rnf09', verbosity=2)`.

## Alcance y limitaciones

- El RNF-09 queda verificado para los casos automatizados descritos; las pruebas no constituyen una demostración de todas las entradas posibles ni de la precisión física de una máquina de corte.
- Los 60,9 + 0,3 + 60,9 cm suman 122,1 cm: no se fuerza su entrada en un tablero de 122 cm ni se cambia su medida para lograrlo.
- Las medidas que ya se hubieran guardado incorrectamente no se pueden reconstruir automáticamente sin conocer la entrada original. No se reescribieron optimizaciones históricas ni sus archivos.
- La prueba de rendimiento RNF-03 documentada previamente corresponde a la revisión que se midió entonces; no se reemplazaron sus resultados por los tiempos de esta suite.
- Corrección preparada para publicación junto con sus pruebas y documentación. Los datos locales y los archivos de la prueba RNF-03 se mantienen fuera de este commit.
