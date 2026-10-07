# Reorganización de la navegación

Fecha: 2026-10-06. Estado: revisado y aprobado por el usuario para publicación en GitHub.

## Problema y resultado

Más opciones concentraba gestión, análisis, preferencias, administración y tutorial en una lista larga. Se sustituye por grupos cortos en la barra:

- Inicio e Historial: accesos principales, también para administradores.
- Gestión: materiales, clientes, proyectos, presupuestos y plantillas.
- Análisis: costos, comparar optimizaciones y estadísticas.
- Ayuda: activa el tutorial existente.
- Cuenta y nombre del usuario: perfil, configuración del sistema y administración de usuarios si corresponde.

Se elimina el saludo separado para evitar repetir el usuario y ahorrar espacio. Se conserva Configuración del sistema hasta revisar sus ajustes. Las rutas y permisos de las vistas no cambian. Los grupos de Gestión y Análisis se omiten si no tienen opciones habilitadas; cada enlace mantiene su condición de perfil previa. La administración conserva la condición de superusuario o rol admin y deja de repetirse.

Tras la revisión, se retiran los dos botones Ver historial del inicio: el de la cabecera y el situado junto al envío del formulario. Historial permanece accesible desde la barra, también en el menú móvil. El formulario conserva Generar plan de corte como acción principal, sin navegación duplicada.

## Diseño

La barra conserva la paleta café. Los desplegables usan fondo de tarjeta, texto de alto contraste, filas de mínimo 48 px y resaltado al pasar el cursor o enfocar. Los controles de apertura son botones, funcionan por clic y mantienen aria-expanded gestionado por Bootstrap.

En móvil los grupos se apilan dentro del menú principal, sin submenús por hover. La altura se limita al espacio de pantalla y permite desplazamiento. Los nombres largos de cuenta se truncan visualmente. Login y registro siguen omitiendo la barra.

## Validación

Antes de publicar pasaron las 86 pruebas de cutless.tests y usuarios.tests, con base de pruebas y archivos temporales. Django check no informó problemas.

Renderizado comprobado con todos los permisos, solo clientes, ningún permiso, administrador y visitante: grupos y enlaces corresponden a las condiciones; administración y tutorial no se duplican. Django check y git diff --check correctos. No se crearon cuentas ni se modificó la base local.

El usuario revisó la navegación y aprobó la retirada de los botones duplicados. La revisión exhaustiva de móvil, oscuro y teclado sigue pendiente. No se renuevan todavía las pantallas internas de cada apartado; se trabajarán de derecha a izquierda: Cuenta, Ayuda, Análisis y Gestión.

Se excluyen los cambios locales previos en base de datos, PDFs y CAMBIOS_AREAS.md.

Archivos: cut/cutless/templates/cutless/base.html, cut/cutless/templates/cutless/index.html y cut/cutless/static/cutless/css/visual-refinement.css.
