# CutLess: cambios de seguridad, primera etapa

Fecha: 2 de octubre de 2026.

## Objetivo y alcance

Esta etapa protege los materiales compartidos del sistema y evita eliminar cuentas mediante una visita a un enlace. Incluye cambios en permisos del servidor, visibilidad de acciones y pruebas automatizadas.

No requiere migraciones, nuevas dependencias ni cambios de configuración. No se modificaron los registros de la base de datos del proyecto.

## 1. Materiales predefinidos del sistema

### Problema anterior

Un usuario autenticado con el permiso `puede_crear_materiales` podía editar materiales predefinidos y eliminarlos si no estaban en uso. Estos materiales son compartidos, de modo que la operación afectaba al catálogo de todos los usuarios.

### Comportamiento actual

- Las vistas de edición y eliminación comprueban si el material es predefinido.
- Si lo es, solo permiten continuar a superusuarios o usuarios cuyo perfil tiene `rol = 'admin'`. Se reutiliza la función existente `es_admin`.
- Un usuario normal recibe HTTP 403 al intentar acceder a estas operaciones sobre materiales predefinidos, incluso mediante una petición directa.
- La lista oculta el enlace de edición de materiales del sistema a usuarios normales.
- Los usuarios conservan la gestión de sus materiales personales. No obtienen acceso a los materiales personales de otros usuarios.
- La comprobación existente que impide eliminar materiales usados en optimizaciones sigue vigente, también para administradores.

La comprobación del servidor es la que aplica el permiso; ocultar el enlace solo ajusta la interfaz. Esta etapa no añade un botón para eliminar materiales predefinidos.

### Archivos afectados

- `cut/cutless/views/materials.py`: comprobaciones de administrador y respuestas HTTP 403.
- `cut/cutless/templates/cutless/lista_materiales.html`: visibilidad del enlace de edición del catálogo compartido.
- `cut/cutless/tests/test_permissions.py`: cinco pruebas nuevas en `MaterialesCompartidosTests`.

## 2. Eliminación de usuarios

### Problema anterior

La vista `eliminar_usuario` eliminaba la cuenta sin comprobar el método HTTP. Un administrador podía activar la operación mediante GET al visitar la URL.

### Comportamiento actual

Se añadió el decorador `require_POST`, después de las comprobaciones existentes de autenticación y rol administrativo.

- Una petición GET de un administrador devuelve HTTP 405 y conserva la cuenta.
- Una petición POST autorizada puede eliminar la cuenta.
- Un usuario normal no puede ejecutar la eliminación.
- Se conserva la restricción que impide al administrador eliminar su propia cuenta desde esta vista.
- La protección CSRF existente sigue activa: un POST sin token válido devuelve HTTP 403.

El formulario del panel administrativo ya usaba POST y token CSRF, por lo que no necesitó modificaciones. Las integraciones que intenten eliminar usuarios mediante GET deberán usar POST con autenticación y CSRF válido.

### Archivos afectados

- `cut/usuarios/views.py`: importación y aplicación de `require_POST`.
- `cut/usuarios/tests.py`: cinco pruebas nuevas en `EliminarUsuarioTests`.

## 3. Validación realizada

Desde `optimizador_materiales/cut` se ejecutaron:

```powershell
python -B manage.py test cutless.tests.test_permissions usuarios.tests --verbosity 1
python -B manage.py check
```

Resultado: **19 pruebas aprobadas** (9 existentes y 10 nuevas). La comprobación de Django no detectó problemas.

Las pruebas utilizaron la base de datos de pruebas de Django, separada de la base de datos del proyecto. No se ejecutó la suite completa en esta etapa.

### Cobertura añadida

| Área | Casos comprobados |
| --- | --- |
| Materiales compartidos | Bloqueo de edición por GET y POST para usuarios normales; ocultación del enlace; bloqueo de eliminación; edición por administrador y superusuario |
| Materiales personales | Edición y eliminación de material propio; rechazo de operaciones sobre material ajeno |
| Cuentas | GET no elimina; POST administrativo elimina; usuario normal no elimina; administrador no se elimina a sí mismo; POST sin CSRF no elimina |

La eliminación de materiales compartidos por administradores y el bloqueo de materiales en uso no tienen pruebas nuevas específicas en esta etapa.

## 4. Trabajo pendiente

Los siguientes hallazgos de la revisión inicial aún no se han corregido:

1. **Completado en la segunda etapa:** asegurar la inserción de datos JSON de materiales en JavaScript. Ver [CAMBIOS_JSON_SEGURO.md](CAMBIOS_JSON_SEGURO.md).
2. **Completado en la tercera etapa:** respetar el margen de corte cero. Ver [CAMBIOS_MARGEN_CERO.md](CAMBIOS_MARGEN_CERO.md).
3. Corregir las conversiones de áreas que usan factores lineales redondeados.
4. Revisar la atomicidad de la persistencia de resultados y los archivos generados.
5. Actualizar las instrucciones de instalación y comprobar visualmente el modo oscuro de los formularios de clientes.

Esta documentación describe exclusivamente los cambios aplicados en la primera etapa; los puntos pendientes no forman parte de la validación anterior.

## 5. Publicar este bloque en GitHub

### Estado del repositorio

El repositorio del proyecto está en `C:\Users\Rick\Documents\ChatGPT\Cutless\optimizador_materiales`. Ya tiene historial, utiliza la rama `main` y tiene configurado el remoto `origin`:

https://github.com/gy0kuroo/optimizador_materiales.git

La carpeta superior `Cutless` también contiene un repositorio Git vacío. Para trabajar con el proyecto existente, ejecutar los comandos dentro de `optimizador_materiales`.

### Preparar el commit de esta etapa

En PowerShell:

```powershell
cd "C:\Users\Rick\Documents\ChatGPT\Cutless\optimizador_materiales"
git status --short
git add cut/cutless/views/materials.py cut/cutless/templates/cutless/lista_materiales.html cut/cutless/tests/test_permissions.py cut/usuarios/views.py cut/usuarios/tests.py docs/CAMBIOS_SEGURIDAD.md
git diff --cached --stat
git diff --cached
```

La revisión debe mostrar los cinco archivos de implementación y pruebas, más este documento. Si hay otros archivos previamente preparados, revisar y retirar del área de preparación los que no correspondan antes de confirmar.

Se observaron cambios locales en `cut/db.sqlite3`, un PDF y otros archivos generados. No corresponden a este bloque y no deben agregarse a este commit. Por ese motivo se enumeran los archivos explícitamente en lugar de usar `git add .`.

### Confirmar y subir

Después de revisar los archivos preparados:

```powershell
git commit -m "fix: restringir materiales compartidos y eliminar usuarios por POST"
git push origin main
```

`git add` prepara los cambios, `git commit` crea una versión local y `git push` la envía a GitHub. Si GitHub solicita autenticación, completar el acceso que indique el gestor de credenciales.

Si el push se rechaza porque el remoto tiene cambios nuevos, no forzar la subida. Revisar la divergencia y resolverla antes de continuar; el proyecto tiene otros cambios locales que se deben conservar.

Para verificar:

```powershell
git log -1 --oneline
git status --short
```

Los archivos de este bloque deberían dejar de aparecer como modificados tras el commit. Los cambios locales ajenos al bloque pueden seguir apareciendo. Comprobar también el nuevo commit en GitHub.

Estos comandos son instrucciones para publicar; la creación del documento no ejecuta `git add`, `git commit` ni `git push`.

## 6. Documentación de los siguientes bloques

Cada bloque de cambios se entregará con documentación actualizada dentro de `docs/`. La documentación acompañará al código y sus pruebas en el mismo commit e incluirá:

- Problema resuelto y comportamiento anterior y actual.
- Archivos afectados.
- Pruebas ejecutadas, resultados y límites de la validación.
- Migraciones, dependencias o pasos de configuración, cuando correspondan.
- Trabajo pendiente y comandos para publicar el bloque.

Este archivo corresponde a la primera etapa de seguridad. Los siguientes bloques podrán tener documentos propios para mantener separado el alcance de cada commit.
