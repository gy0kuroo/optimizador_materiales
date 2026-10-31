# Versión de Python para Render

Fecha: 30 de octubre de 2026.

## Decisión

Se declara Python 3.13.12 en `.python-version`, en la raíz del repositorio Git. Coincide con el intérprete local utilizado en las comprobaciones del proyecto y evita depender de la versión predeterminada de los servicios nuevos de Render.

El archivo no instala ni cambia Python en el computador. Tampoco modifica dependencias, datos ni funciones de CutLess. La instalación limpia de las dependencias en Linux y las pruebas de exportaciones siguen pendientes para la preparación del despliegue; igualar la versión no certifica por sí solo esa compatibilidad.

## Configuración futura

Render admite `.python-version` en la raíz del repositorio. Su variable `PYTHON_VERSION` tiene prioridad sobre el archivo: si ya existe en el servicio, deberá coincidir con 3.13.12 o retirarse al configurar el despliegue. No se ha accedido al panel de Render ni cambiado variables remotas.

Fuente: https://render.com/docs/python-version

## Verificación

Se comprobó `python --version` (3.13.12), la coincidencia con el archivo y su formato de una sola línea. No se añaden pruebas de aplicación para un archivo declarativo sin cambios de lógica.

Publicación autorizada el 30 de octubre de 2026; sin despliegue.
