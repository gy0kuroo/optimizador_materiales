# CutLess: serialización segura de materiales, segunda etapa

Fecha: 2 de octubre de 2026.

## Problema y comportamiento actual

Los nombres de materiales se incorporaban a bloques JavaScript mediante `json.dumps` y el filtro `safe`. Un nombre con `</script>` podía cerrar el bloque e introducir contenido HTML ejecutable. El problema afectaba al formulario principal y a la edición de optimizaciones; la carga de plantillas reutiliza el formulario principal.

Ahora las vistas entregan un diccionario `materiales_data`. Las dos plantillas lo serializan con el filtro de Django `json_script` en un elemento `script` de tipo `application/json`, cuyo identificador es `materiales-data`. Este filtro escapa los caracteres `<`, `>` y `&`. JavaScript recupera los datos con `JSON.parse` sobre el `textContent` del elemento, sin incorporarlos como código ejecutable.

Los nombres originales, sus caracteres especiales y los precios se conservan tras la lectura del JSON. El formulario principal mantiene `window.materialData`, utilizado por la selección automática de medidas y precios. Se conservan los filtros de materiales propios y predefinidos, excluyendo los personales de otros usuarios.

## Formularios con errores

La edición prepara los datos de materiales antes de procesar GET o POST y los incluye también en las respuestas con errores de validación. Esto evita que un formulario inválido intente usar una variable que antes solo se inicializaba en GET. Las rutas de error del formulario principal también usan el contexto actualizado.

## Archivos afectados

- `cut/cutless/views/common.py`: el auxiliar se renombra a `_materiales_data_index` y devuelve un diccionario.
- `cut/cutless/views/optimization.py`: contextos de creación, edición y errores; se retira la serialización manual y se prepara el contexto de edición para POST inválidos.
- `cut/cutless/views/plantillas.py`: contexto de materiales al cargar una plantilla.
- `cut/cutless/templates/cutless/index.html`: `json_script` y lectura con `JSON.parse`.
- `cut/cutless/templates/cutless/editar_optimizacion.html`: `json_script` y lectura con `JSON.parse`.
- `cut/cutless/tests/test_materiales_json.py`: cinco pruebas de regresión.
- `docs/CAMBIOS_SEGURIDAD.md`: actualización del punto pendiente de la primera etapa.
- `docs/CAMBIOS_JSON_SEGURO.md`: documentación de este bloque.

No requiere migraciones, nuevas dependencias ni cambios de configuración.

## Validación

Las cinco pruebas nuevas comprueban el formulario principal, la edición, la carga de plantillas, un POST inválido al formulario principal y un POST inválido a la edición.

En cada respuesta se verifica que haya un único bloque JSON de datos, que no contenga `<`, `>` ni `&` literales, que el nombre malicioso se conserve como dato tras deserializar, que el precio sea correcto y que no aparezcan materiales privados de otro usuario. También se comprueba la presencia de la lectura con `JSON.parse`.

Comando para ejecutar las pruebas de seguridad desde la raíz del repositorio:

```powershell
python -B cut/manage.py test cutless.tests.test_materiales_json cutless.tests.test_permissions usuarios.tests --verbosity 1
```

Además, se ejecutó la suite completa de `cutless.tests` y `usuarios.tests`: **40 pruebas aprobadas**, sin problemas detectados por las comprobaciones de Django. Para esta ejecución se configuraron `MEDIA_ROOT` y la caché de Matplotlib en una carpeta temporal, y se usó la base de datos de pruebas de Django. La primera ejecución aislada quedó bloqueada por permisos del entorno temporal; al repetir con los permisos necesarios, todas las pruebas pasaron.

Se verificó mediante SHA-256 que `cut/db.sqlite3` y `cut/media/pdfs/optimizacion_1.pdf` no cambiaron durante la ejecución completa.

No se realizó una prueba visual ni una ejecución de JavaScript en navegador. Las pruebas comprueban el HTML y el JSON generado por Django; este bloque no constituye una auditoría completa de todas las posibles fuentes de XSS de la aplicación.

## Publicación en GitHub

Desde `C:\Users\Rick\Documents\ChatGPT\Cutless\optimizador_materiales`:

```powershell
git add cut/cutless/views/common.py cut/cutless/views/optimization.py cut/cutless/views/plantillas.py cut/cutless/templates/cutless/index.html cut/cutless/templates/cutless/editar_optimizacion.html cut/cutless/tests/test_materiales_json.py docs/CAMBIOS_SEGURIDAD.md docs/CAMBIOS_JSON_SEGURO.md
git diff --cached --check
git diff --cached --stat
git commit -m "fix: serializar materiales con json_script"
git push origin main
```

Agregar únicamente los archivos de este bloque. Los cambios locales de la base de datos y archivos generados no corresponden a este commit.

## Siguiente prioridad

El margen de corte cero se corrigió en la tercera etapa: [CAMBIOS_MARGEN_CERO.md](CAMBIOS_MARGEN_CERO.md). Las conversiones de áreas se corrigieron en la cuarta etapa: [CAMBIOS_AREAS.md](CAMBIOS_AREAS.md). La siguiente prioridad es revisar la persistencia de resultados.
