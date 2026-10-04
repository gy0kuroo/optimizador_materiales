# CutLess: persistencia de resultados ante fallos, quinta etapa

Fecha: 3 de octubre de 2026.

## Problema resuelto

El guardado eliminaba los tableros anteriores antes de terminar las nuevas imágenes y el PDF. También eliminaba el PDF anterior antes de guardar su reemplazo. Si fallaba el disco, la generación del PDF o la base de datos, el resultado podía quedar incompleto.

Las vistas guardaban los parámetros de una edición, o creaban una optimización nueva, antes de persistir el resultado. Un fallo posterior dejaba una edición sin resultados coherentes o una creación incompleta.

Además, el PDF intermedio usaba un nombre basado en el número mostrado en el historial. Ese número puede repetirse entre usuarios, por lo que distintas optimizaciones podían escribir en la misma ruta intermedia.

## Comportamiento actual

1. Se comprueba que haya imágenes, que coincidan con los tableros y que el Base64 sea válido antes de escribir.
2. El servicio inicia una transacción. Para una optimización existente, consulta su estado anterior con `select_for_update`; para una nueva, inserta el registro dentro de la misma transacción.
3. Las nuevas imágenes y el PDF reciben nombres únicos. El PDF se genera en un buffer de memoria, sin una ruta intermedia compartida.
4. Se reemplazan los registros de tableros y se guardan juntos los parámetros, estadísticas y referencias a los archivos nuevos.
5. Después de confirmar la transacción, se retiran las imágenes y el PDF anteriores mediante `on_commit`.

Si se produce una excepción durante el guardado, se revierte la transacción y se retiran los archivos nuevos registrados, incluidos los de una escritura parcial que conserve el nombre previsto. El resultado anterior permanece disponible. Una creación fallida no deja un registro nuevo en la base de datos.

La regeneración independiente del PDF sigue el mismo principio: conservar el archivo anterior hasta confirmar la referencia al nuevo. Un fallo al retirar archivos se registra en el log y no invalida un resultado ya confirmado.

Los nombres de descarga siguen siendo `optimizacion_N.pdf` y `optimizacion_N.png`. Los nombres internos llevan identificadores únicos y pueden cambiar al recalcular.

## Archivos afectados

- `cut/cutless/services/optimization.py`: transacciones, escritura de archivos con nombres únicos, PDF en memoria, retirada de archivos tras el commit y limpieza tras fallos.
- `cut/cutless/views/optimization.py`: delega la inserción y el guardado de parámetros al servicio; prepara el número del historial antes de guardar una instancia nueva.
- `cut/cutless/exports/pdf.py`: parámetro opcional `archivo_salida` para generar el PDF en un buffer. Sin ese parámetro conserva la interfaz de exportación a disco.
- `cut/cutless/tests/test_persistencia.py`: quince pruebas nuevas con transacciones reales de prueba.
- `docs/CAMBIOS_SEGURIDAD.md` y `docs/CAMBIOS_AREAS.md`: estado y siguiente prioridad actualizados.
- `docs/CAMBIOS_PERSISTENCIA.md`: documentación de esta etapa.

No requiere migraciones, nuevas dependencias ni cambios de configuración.

## Validación

**69 pruebas aprobadas** en la suite completa de `cutless.tests` y `usuarios.tests`. Django no detectó problemas de configuración.

Las quince pruebas nuevas cubren:

- Fallos al generar el PDF, guardar el PDF y escribir parcialmente una imagen.
- Fallos de base de datos al guardar un tablero o la optimización final.
- Reemplazo correcto y retirada de los tres archivos anteriores: tablero, vista previa y PDF.
- Creación fallida en el servicio y desde el formulario, sin registros nuevos.
- Edición fallida desde el formulario, conservando los parámetros anteriores.
- PDFs de distintos usuarios con el mismo número del historial, sin sobrescribir archivos.
- Fallo de generación o de guardado de la referencia de un PDF independiente.
- Reemplazo independiente del PDF sin alterar imágenes ni registros de tableros.
- Imágenes vacías, Base64 inválido y datos sin tableros.
- Fallo de limpieza registrado en el log sin revertir un resultado confirmado.

Las pruebas comprueban tanto las filas de la base de datos como los nombres y bytes de los archivos anteriores, y la ausencia de nuevos archivos después de fallos controlados. Se ejecutaron con la base de datos de pruebas y una carpeta temporal para archivos y caché de Matplotlib. Los hashes SHA-256 de `cut/db.sqlite3` y `cut/media/pdfs/optimizacion_1.pdf` permanecieron iguales durante la ejecución.

El procedimiento para reproducir la suite completa en una carpeta temporal está en [CAMBIOS_MARGEN_CERO.md](CAMBIOS_MARGEN_CERO.md#validación). No se realizó una prueba visual ni una prueba de concurrencia entre procesos.

## Límites y datos existentes

- La transacción protege la base de datos; el almacenamiento de archivos tiene una limpieza compensatoria. Un apagado abrupto del proceso o un fallo de permisos al eliminar puede dejar archivos sin referencia. Esos casos no tienen reparación automática en este bloque.
- La eliminación posterior al commit registra sus errores. Un archivo antiguo que no pueda eliminarse permanece en disco, pero el resultado nuevo sigue siendo válido.
- No se añaden migraciones ni una limpieza masiva de archivos históricos. Los archivos antiguos de una optimización se retiran cuando esa optimización se recalcula correctamente.
- SQLite no ofrece el bloqueo por fila de `select_for_update`. No se garantiza en esta etapa la edición concurrente de una misma optimización entre procesos.
- Si un futuro llamador añade una transacción exterior y la revierte después de que el servicio haya terminado, puede dejar archivos nuevos sin referencia. Las vistas actuales no añaden esa transacción exterior.
- Los errores de generación o almacenamiento siguen propagándose como errores de la petición; este bloque protege los datos, pero no añade una pantalla de recuperación específica.
- El exportador directo a disco conserva su comportamiento anterior. Las rutas de persistencia de optimizaciones usan el buffer; los PDFs de presupuestos no forman parte de esta corrección.

## Publicación en GitHub

Desde la raíz de `optimizador_materiales`:

```powershell
git add cut/cutless/services/optimization.py cut/cutless/views/optimization.py cut/cutless/exports/pdf.py cut/cutless/tests/test_persistencia.py docs/CAMBIOS_SEGURIDAD.md docs/CAMBIOS_AREAS.md docs/CAMBIOS_PERSISTENCIA.md
git diff --cached --check
git diff --cached --stat
git commit -m "fix: guardar resultados completos y conservar archivos ante fallos"
git push origin main
```

La base de datos y los archivos generados locales quedan fuera del commit.

## Siguiente prioridad

La configuración por entorno y el acceso privado a archivos se prepararon en la sexta etapa: [CAMBIOS_PRODUCCION.md](CAMBIOS_PRODUCCION.md). Quedan actualizar las instrucciones de instalación y comprobar los formularios de clientes en modo oscuro; el despliegue real requiere configurar la infraestructura.
