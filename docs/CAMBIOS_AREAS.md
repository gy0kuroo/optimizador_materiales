# CutLess: conversiones precisas de áreas, cuarta etapa

Fecha: 3 de octubre de 2026.

## Problema resuelto

Las conversiones de áreas elevaban al cuadrado el resultado de `convertir_desde_cm(1, unidad)`. Esa función redondea las longitudes a dos decimales, por lo que el factor de conversión perdía precisión antes de calcular el área.

En pies se usaba `0.03²` en lugar de `(1 / 30.48)²`. En pulgadas se usaba `0.39²` en lugar de `(1 / 2.54)²`.

| Área original | Antes | Ahora |
| --- | --- | --- |
| 1 m² expresado en ft² | 9 ft² | 10,76 ft² |
| 1 m² expresado en in² | 1521 in² | 1550 in² |

El error anterior en pies cuadrados era aproximadamente del 16,4 % por debajo del valor correcto. No afectaba al número de tableros calculado por el motor, que trabaja en centímetros.

## Solución

Se añadió `obtener_factor_area_desde_cm2(unidad)` en `units.py`. Calcula el factor como `1 / centimetros_por_unidad²` sin redondear el factor lineal. Cada salida redondea el área final a dos decimales, como antes.

Admite cm², m², mm², in² y ft², conserva el alias `pulgadas` y el comportamiento de usar cm² para unidades desconocidas. Se mantienen las conversiones y el redondeo existentes de las dimensiones lineales.

El factor preciso se aplica al contexto de resultados, las áreas usadas y de desperdicio de los gráficos, la lista de piezas del Excel y las áreas unitarias, totales y por tablero del PDF de optimización.

## Archivos afectados

- `cut/cutless/units.py`: factor de conversión de áreas sin redondeo previo.
- `cut/cutless/services/optimization.py`: áreas totales y por tablero en el contexto de resultados.
- `cut/cutless/render.py`: áreas mostradas en los gráficos.
- `cut/cutless/exports/excel.py`: áreas unitarias y totales de piezas.
- `cut/cutless/exports/pdf.py`: áreas de piezas y resumen por tablero.
- `cut/cutless/tests/test_areas.py`: seis pruebas nuevas.
- `docs/CAMBIOS_SEGURIDAD.md`, `docs/CAMBIOS_JSON_SEGURO.md` y `docs/CAMBIOS_MARGEN_CERO.md`: referencias al bloque completado.
- `docs/CAMBIOS_AREAS.md`: documentación de esta etapa.

No requiere migraciones, dependencias nuevas ni cambios de configuración.

## Validación

**54 pruebas aprobadas** en la suite completa de `cutless.tests` y `usuarios.tests`. Django no detectó problemas de configuración.

Las seis pruebas nuevas comprueban:

1. Equivalencias conocidas de un metro cuadrado en las cinco unidades.
2. Alias de pulgadas y compatibilidad con unidades desconocidas.
3. Conversión de áreas totales y por tablero sin modificar el diccionario original.
4. Áreas unitarias y totales en un Excel real, leído con openpyxl, para las cinco unidades.
5. Texto de área correcta en un gráfico real generado con Matplotlib.
6. Generación de un PDF y textos de áreas unitarias, totales, usadas y de desperdicio enviados a ReportLab.

Las pruebas de gráficos y PDF capturan las llamadas de dibujo y ejecutan las funciones originales. No son una validación visual del diseño ni una extracción del texto del PDF terminado. La prueba de PDF resuelve la ruta relativa devuelta por el exportador contra `MEDIA_ROOT`.

La suite utilizó una base de datos de pruebas y archivos en una carpeta temporal. Se verificó mediante SHA-256 que `cut/db.sqlite3` y `cut/media/pdfs/optimizacion_1.pdf` permanecieran intactos. El procedimiento de ejecución aislada está en [CAMBIOS_MARGEN_CERO.md](CAMBIOS_MARGEN_CERO.md#validación).

## Resultados anteriores

Las áreas guardadas en la base de datos siguen en cm² y no requieren migración. La pantalla convierte esas áreas con el factor corregido al cargar el resultado.

Los gráficos y PDF ya persistidos conservan su contenido anterior. Para actualizarlos hay que editar y recalcular la optimización; descargar un PDF que ya existe reutiliza ese archivo. Las nuevas exportaciones Excel emplean el factor corregido.

## Publicación en GitHub

Desde la raíz de `optimizador_materiales`:

```powershell
git add cut/cutless/units.py cut/cutless/services/optimization.py cut/cutless/render.py cut/cutless/exports/excel.py cut/cutless/exports/pdf.py cut/cutless/tests/test_areas.py docs/CAMBIOS_SEGURIDAD.md docs/CAMBIOS_JSON_SEGURO.md docs/CAMBIOS_MARGEN_CERO.md docs/CAMBIOS_AREAS.md
git diff --cached --check
git diff --cached --stat
git commit -m "fix: convertir areas sin redondear factores"
git push origin main
```

La base de datos y los archivos generados locales quedan fuera de este commit.

## Siguiente prioridad

Revisar la persistencia de resultados para evitar datos parciales y problemas con los archivos generados cuando falla una operación.
