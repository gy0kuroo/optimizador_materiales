# Datos locales y archivos generados fuera de Git

Fecha: 30 de octubre de 2026.

## Decisión

El usuario confirmó que los registros, optimizaciones y archivos históricos son de prueba y no requieren migración. Producción comenzará con una base limpia; no se realizó todavía ninguna operación en Supabase.

## Cambio

Se retiraron únicamente del índice Git, mediante git rm --cached:

- Una base SQLite: cut/db.sqlite3.
- 29 archivos generados en cut/media/ (PDF e imágenes).
- 167 archivos recopilados en cut/staticfiles/.

Total: 197 archivos. Las reglas existentes de .gitignore ya excluyen estas rutas, por lo que no fue necesario modificarlas. Los archivos estáticos fuente en las aplicaciones y las migraciones continúan versionados. Los archivos recopilados se regeneran mediante collectstatic.

Se conservaron todos los archivos en el computador: se compararon sus hashes SHA-256 antes y después de retirar el seguimiento y coincidieron. No se abrió la base de datos ni se consultaron registros; la comprobación leyó los bytes para calcular hashes.

El usuario autorizó publicar las bajas el 30 de octubre de 2026 junto con la preparación de producción. La operación no elimina las copias contenidas en commits anteriores ni reescribe el historial.

## Instalaciones nuevas

Una clonación futura de la versión con estas bajas no incluirá base local ni resultados de prueba. Las tablas se crearán mediante las migraciones cuando se autorice esa etapa; los archivos de usuarios se producirán a partir de nuevas optimizaciones. No se trasladarán automáticamente cuentas ni datos de prueba anteriores.

El almacenamiento persistente y privado de los nuevos PDF e imágenes sigue pendiente de definir para producción.
