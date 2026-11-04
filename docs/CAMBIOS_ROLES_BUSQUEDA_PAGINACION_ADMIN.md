# Cambios en roles y administración de usuarios

Fecha: 3 de noviembre de 2026.

## Objetivo

Separar el uso normal de CutLess de las funciones administrativas y mejorar la gestión de usuarios sin alterar el estilo establecido por las pantallas de gestión.

## Roles y permisos

- El rol Administrador conserva el acceso al flujo normal de CutLess, incluida la entrada al flujo de optimización.
- El acceso al dashboard y a las vistas administrativas se mantiene protegido mediante `es_admin()`.
- La lógica central de permisos dejó de usar al rol administrador como una excepción global; las funcionalidades restringidas se evalúan explícitamente.
- Los usuarios normales siguen sin poder acceder al dashboard de administración ni ven su enlace administrativo en la navegación.
- Se añadieron pruebas de regresión para el acceso administrativo, el flujo normal del administrador y la navegación según rol.

## Búsqueda y presentación del dashboard

- El dashboard permite buscar usuarios por nombre de usuario, correo electrónico o rol mediante un formulario GET.
- La búsqueda conserva el término ingresado, presenta el estado vacío cuando no hay coincidencias y permite volver al listado completo.
- Se reorganizó la pantalla siguiendo el patrón de las páginas de gestión: cabecera, panel de búsqueda, listado y, en una sección independiente al final, creación de usuario.
- El panel usa las reglas existentes de `management-refinement.css` para mantener tipografía, controles, espacios y colores coherentes con el resto de CutLess.

## Paginación y acciones

- El listado muestra hasta 10 usuarios por página y presenta controles «Anterior» y «Siguiente» con flechas solo cuando hay más de una página.
- La paginación se aplica después de la búsqueda y mantiene el término de búsqueda al cambiar de página.
- Se muestra el número de página actual y el total de páginas.
- Las acciones Editar y Eliminar se alinean a la derecha; Eliminar usa una variante de contorno y conserva la confirmación existente.
- El selector de rol queda en su columna y «Actualizar rol» aparece solo cuando el valor cambia. Su envío conserva el POST existente y utiliza el indicador de carga compartido.

## Rediseño visual del dashboard

- La tabla combina nombre, inicial y correo en una columna; agrupa los indicadores Staff y Activo en Estado y deja Rol y Acciones en columnas ajustadas al contenido.
- El usuario actual se identifica con un badge; los emails vacíos muestran «Sin email» y los usuarios propios muestran «Sin acciones».
- Staff, Activo e Inactivo se presentan con badges tenues, sin rellenos sólidos. Los estilos de acento, éxito, peligro, superficie y foco usan los tokens compartidos de tema claro y oscuro.
- El buscador, Buscar y Quitar filtro comparten una fila y una altura real de 48 px. Quitar filtro solo aparece al buscar; el contador muestra el total filtrado de forma discreta sobre la tabla.
- En escritorio las acciones quedan en una fila a la derecha. Bajo 768 px cada usuario se presenta como tarjeta, y el formulario se apila en una columna sin desbordamiento horizontal.
- El formulario de creación usa dos columnas en escritorio, conserva las ayudas y reglas de contraseña de Django, coloca estas reglas en un bloque común y presenta los errores junto a cada campo.
- El botón superior conserva la acción primaria; desplaza al formulario y enfoca el primer campo. El botón final del formulario conserva la acción de éxito y el estado de carga compartido.
- Los cambios se limitan a la plantilla y CSS de presentación y a una interacción local para habilitar el guardado del rol cuando hay una diferencia. No cambian permisos, rutas, filtros, validaciones ni operaciones de datos.

## Archivos involucrados

- `cut/usuarios/views.py`: permisos administrativos, búsqueda y paginación del dashboard.
- `cut/usuarios/templates/usuarios/admin_dashboard.html`: estructura, controles de búsqueda, listado y navegación entre páginas.
- `cut/cutless/static/cutless/css/management-refinement.css`: presentación de acciones y paginación del dashboard.
- `cut/usuarios/tests.py`: pruebas de búsqueda, paginación y estructura accesible del dashboard.
- `cut/cutless/views/common.py` y `cut/cutless/views/optimization.py`: permisos por funcionalidad y flujo normal de optimización.
- `cut/cutless/tests/test_permissions.py` y `cut/cutless/tests/test_shell_navigation.py`: regresiones de roles y navegación.

No se añadieron migraciones ni se modificó el esquema de datos.

## Verificación

Se ejecutó la batería de usuarios, permisos y navegación:

```text
python manage.py test usuarios.tests cutless.tests.test_permissions cutless.tests.test_shell_navigation --verbosity 2
```

Resultado: 39 pruebas aprobadas y ninguna incidencia en las comprobaciones del sistema Django.

La vista también se revisó en navegador a 390, 768, 900, 1024 y 1440 px, en ambos temas. No se observó desbordamiento horizontal; las acciones permanecen alineadas en los anchos de escritorio e intermedios. El badge Staff alcanza un contraste medido de 5.78:1 en claro y 5.56:1 en oscuro.
