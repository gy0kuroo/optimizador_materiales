# Cambios: documentación de instalación

Fecha: 2026-10-04.

## Problema

El README enlazaba GUIA_RAPIDA.md y setup_project.py, que no existen, indicaba redirecciones antiguas ausentes y describía formularios y pruebas como archivos en lugar de paquetes. También proponía borrar la base de datos como solución de problemas.

## Cambio

Se reescribió README.md con la URL real del repositorio y comandos desde su raíz. El entorno virtual se invoca directamente para evitar problemas de activación en PowerShell. Incluye migraciones, comprobaciones, creación opcional del administrador, catálogo opcional, inicio del servidor y alternativa Linux/macOS.

Se explica que .env.example no se carga automáticamente, cómo definir variables y dónde consultar la configuración de producción. Las pruebas usan archivos temporales y cubren cutless.tests y usuarios.tests. Se corrigieron la estructura, las rutas y los enlaces a documentación. Se retiró la instrucción de borrar la base.

## Validación

- check, migrate --noinput, check_database y crear_materiales_predefinidos terminaron correctamente con una base SQLite temporal nueva.
- check_database confirmó las tablas esenciales después de migrar.
- El hash de la base local coincidió antes y después.
- La instalación de dependencias y la creación interactiva del administrador no se ejecutaron: se usó el Python existente y no se crearon cuentas reales.

Este bloque modifica únicamente documentación. Los cambios locales previos en datos, PDFs y CAMBIOS_AREAS.md se mantienen fuera del commit.

## Pendiente

La revisión de legibilidad de los formularios de clientes en modo oscuro corresponde al siguiente bloque separado. El despliegue real y la retirada de datos versionados siguen pendientes.
