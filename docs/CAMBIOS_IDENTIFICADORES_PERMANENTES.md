# Identificadores permanentes de optimización

Fecha: 23/10/2026. Estado: revisado y autorizado para publicación junto con los nombres opcionales.

## Problema

El número visible dependía de la posición del trabajo en una consulta. Al borrar una optimización o cambiar el orden, podía cambiar la identificación de los demás trabajos. Historial, presupuestos, mensajes y descargas calculaban esa posición por separado.

## Solución

Cada optimización expone un código como **OPT-0006**, derivado de su clave primaria existente mediante la propiedad `Optimizacion.codigo`. Se usan al menos cuatro dígitos; números mayores no se truncan. No se crea una secuencia visual por usuario ni se vuelve a contar el historial.

- Borrar OPT-0005 deja OPT-0004, OPT-0006 y OPT-0007 con sus códigos originales.
- Ordenar, filtrar, marcar favoritos o editar no cambia el código.
- Las claves pertenecen al conjunto de registros de la aplicación: puede haber saltos por eliminaciones o registros de otros usuarios. El código no revela esos datos ni modifica los controles de acceso.
- Duplicar carga el trabajo original con su referencia correcta. Al guardar una nueva optimización se asigna una clave nueva y, por tanto, un código nuevo.
- «Tablero X de N» sigue siendo la posición de un tablero dentro de su optimización. No se sustituye por el código del trabajo.

La propiedad reutiliza los identificadores ya guardados. No requiere migración, renumeración de registros ni cambios en claves foráneas, URLs, coordenadas o cálculos. Los registros anteriores reciben su código según su clave real, que puede diferir del antiguo número de posición.

## Alcance

- Historial y visor, resultado, edición, eliminación, duplicación y favoritos.
- Mensajes de optimización completada y referencias en proyectos, presupuestos, comparación, estadísticas e historial de costos/clientes.
- Impresión, PDF y Excel de la optimización, PNG por tablero y referencias de optimización en el PDF de presupuesto.
- Los selectores de modelos identifican el registro también mediante su representación textual.

Los nombres de descarga son `OPT-0006.pdf`, `OPT-0006.xlsx` y `OPT-0006_tablero-2.png`. El código también aparece dentro de los documentos del plan de corte. No se renombran archivos ya descargados ni se sobrescriben imágenes o PDF históricos guardados; las nuevas descargas usan el código permanente.

En el resultado se muestra únicamente el código bajo el título, sin repetir la cantidad de tableros ni el porcentaje del gráfico global.

La función antigua `calcular_numero_lista` conserva su firma para compatibilidad, pero devuelve la clave estable; se retiraron los bucles que calculaban posiciones en los apartados relacionados.

## Verificación

- **152 pruebas correctas** con base de datos y archivos temporales independientes.
- Nuevas pruebas de eliminación intermedia, cuatro ordenamientos, filtro, eliminación del último registro y creación posterior, nombres de descarga independientes de una posición, mensajes y contenido PDF/Excel.
- Revisión visual en una base de datos de prueba: se crearon siete optimizaciones y se eliminó la quinta; siguen visibles OPT-0006 y OPT-0007.
- `manage.py check`, comprobación de sintaxis JavaScript y `makemigrations --check --dry-run` correctos; no hay cambios de esquema.

## Etapa siguiente

Los nombres descriptivos opcionales («Mueble de cocina», por ejemplo) se implementaron en una segunda etapa, documentada en [CAMBIOS_NOMBRES_OPTIMIZACIONES.md](CAMBIOS_NOMBRES_OPTIMIZACIONES.md). El código fijo conserva su función de identificación. Ambas etapas se incluyen en el mismo commit, con publicación autorizada por el usuario.
