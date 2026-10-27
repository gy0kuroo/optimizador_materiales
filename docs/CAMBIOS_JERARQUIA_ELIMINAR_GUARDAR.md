# Jerarquía visual de eliminar y guardar

Fecha: 26 de octubre de 2026.

## Cambios

- Los botones «Eliminar» de cada tipo de pieza pasan de relleno sólido a contorno, tanto al preparar un corte como al editarlo. Conservan el texto, la papelera y su posición a la derecha. Las filas nuevas clonadas heredan la misma variante.
- En claro utilizan el burdeos semántico; en oscuro, la tinta roja clara del tema. El fondo normal es transparente, al pasar el cursor aparece un tinte tenue y mientras se presiona se muestra el relleno rojo con texto blanco.
- La confirmación final de una eliminación conserva su botón rojo sólido. No se modifican el comportamiento de eliminar filas ni las confirmaciones existentes.
- Los botones de preferencias, datos de cuenta y contraseña se alinean a la derecha del formulario en escritorio. En pantallas de hasta 767 px ocupan todo el ancho disponible. Mantienen el verde de guardado; no se añade otra acción cobre que compita con ellos.
- Se actualizan las versiones de las hojas de estilos para evitar que la caché conserve la presentación anterior.

## Alcance

Cambios de presentación en inicio, edición y perfil. Los colores proceden de los tokens semánticos del tema compartido. No se cambian textos, rutas, cálculos ni datos guardados.

La variante de contorno se aplica a la eliminación repetida de filas de piezas; no se sustituye indiscriminadamente todo botón destructivo del sistema.

## Verificación

Las tres plantillas afectadas compilan correctamente. Pasan 26 pruebas de usuarios, vistas y revisión de usabilidad, con base de datos y archivos temporales aislados. El diff no presenta incidencias de espacios. El usuario revisó y aprobó la presentación en su navegador.

Ajuste aprobado para publicación junto con su documentación. Los datos locales y los pendientes de otras tareas quedan fuera del commit.
