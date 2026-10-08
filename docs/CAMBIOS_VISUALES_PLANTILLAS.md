# Plantillas: presentación, unidades y copias personales

Fecha: 7 de octubre de 2026. Bloque revisado y aprobado por el usuario para publicación.

## Presentación

La biblioteca y las pantallas de crear, editar y eliminar utilizan una hoja propia, `templates-refinement.css`, para conservar la paleta, el tema oscuro, letras de 1.125 rem y botones de al menos 48 px sin afectar otras pantallas.

- Búsqueda con etiquetas visibles para nombre y categoría, filtros alineados y acción Quitar filtros.
- Tarjetas con acciones descriptivas: Cargar plantilla, Editar y Eliminar. La cantidad se identifica como tipos de pieza.
- Las plantillas del sistema ofrecen Crear copia personal y explican que la original se conserva.
- Formularios con checkbox de 24 px integrado, ayudas legibles y ejemplo breve del formato de piezas. Se aclaran las unidades seleccionadas y el uso de punto para decimales.
- Confirmación de eliminación con la misma presentación. Se conservan el formulario POST y la protección CSRF.

## Correcciones funcionales

- El formulario convierte las dimensiones del tablero desde la unidad elegida a centímetros al guardar, y las vuelve a convertir al editar. Las piezas mantienen sus medidas en la unidad seleccionada.
- El margen se presenta en milímetros y se almacena en centímetros. Se conserva el valor cero y se valida el rango de 0 a 10 mm. Una plantilla nueva propone 3 mm.
- Personalizar una plantilla predefinida crea una copia propiedad del usuario, sin modificar el registro compartido.
- Los nombres duplicados se muestran como error del formulario. Las medidas negativas y los valores no finitos se rechazan.
- Se conserva la protección frente a editar, cargar o eliminar plantillas privadas de otros usuarios.

## Verificación

Pasaron 18 pruebas: las 14 existentes de permisos y cuatro nuevas para Plantillas. Cubren creación, edición y carga en metros con margen cero; copia del sistema sin modificar el original; validación de nombres y medidas; y rechazo de acceso a plantillas ajenas.

El usuario aprobó la revisión visual; no se han automatizado todas las combinaciones de tema y ancho de ventana. No requiere migraciones ni se han modificado los datos locales del usuario. Este bloque se publica junto con las mejoras de Gestión y separado del commit de Análisis.
