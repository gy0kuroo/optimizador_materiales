# Instalación de dependencias desde la raíz

Fecha de implementación: 10 de octubre de 2026. Publicación autorizada por el usuario el 19 de octubre de 2026.

## Problema observado

El usuario indicó que tuvo que instalar las dependencias una por una desde la raíz del proyecto. No se dispone del comando literal ni del mensaje de error, por lo que no puede confirmarse la causa exacta de aquella instalación.

La revisión encontró que la lista estaba únicamente en `cut/requirements.txt`. Un comando habitual como `python -m pip install -r requirements.txt` fallaba desde la raíz por no existir allí ese archivo. Además, `pip install requirements`, sin `-r`, busca un paquete y no lee la lista del proyecto.

## Corrección

- Se agrega `requirements.txt` en la raíz, que incluye la lista existente mediante `-r cut/requirements.txt`. Las versiones se mantienen en un solo lugar y los comandos antiguos que apuntan a `cut/requirements.txt` siguen funcionando.
- El README usa el Python del entorno virtual, incluye actualización de pip y comprobación con `pip check`, y explica la opción `-r` y la carpeta desde donde ejecutar el comando.
- Se aclara que sqlparse y tzdata son dependencias de Django, en lugar de presentarlas como opcionales.
- No se cambian versiones sin evidencia de incompatibilidad.

## Validación

La resolución inicial con Python 3.13.12 en Windows de 64 bits encontró paquetes binarios para toda la lista, incluidas las versiones actuales de Matplotlib y Pillow. La instalación completa desde el archivo de la raíz terminó correctamente en un entorno virtual temporal independiente. `pip check` no detectó conflictos, `manage.py check` terminó sin incidencias y pasaron las 115 pruebas de `cutless.tests` y `usuarios.tests`. Los archivos de prueba se mantuvieron fuera de los datos del usuario y el entorno temporal se eliminó al terminar.

No se modifica el Python habitual, la base de datos ni los archivos del usuario. Esta revisión no garantiza compatibilidad con versiones de Python o arquitecturas diferentes de las comprobadas.
