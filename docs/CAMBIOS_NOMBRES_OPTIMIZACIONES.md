# Nombres opcionales de los trabajos

Fecha: 24/10/2026. Estado: revisado y autorizado para publicación junto con los códigos permanentes.

## Comportamiento

El código permanente (por ejemplo, OPT-0006) sigue identificando la optimización. Ahora puede acompañarse de un nombre opcional como «Mueble de cocina».

- Al preparar o editar una optimización, aparece el campo **Nombre del trabajo (opcional)**. Puede quedar vacío y admite hasta 100 caracteres. Se normalizan los espacios repetidos.
- En el historial, el nombre aparece como título y el código debajo. Sin nombre, se conserva la presentación basada únicamente en el código. Los nombres largos se limitan visualmente a dos líneas y el título emergente conserva el texto completo.
- En el resultado se muestran nombre y código sin repetir los porcentajes ni el número de tableros del gráfico.
- **Cambiar nombre**, en Más opciones del historial, y **Nombrar trabajo/Cambiar nombre**, en el resultado, abren un formulario específico. Guardar ahí actualiza exclusivamente el nombre: no vuelve a calcular ni reemplaza piezas, imágenes, PDF, cantidades, fecha o estadísticas.
- Vaciar el nombre restaura la presentación basada en el código; no elimina el trabajo.
- Dos optimizaciones pueden tener el mismo nombre, porque sus códigos las distinguen. Duplicar copia el nombre como dato inicial y genera un código distinto al guardar el nuevo cálculo.
- La búsqueda del historial encuentra nombres de trabajos, nombres de piezas y referencias OPT-0006. Se conserva el parámetro anterior `nombre_pieza` para no romper enlaces y filtros. Los términos se codifican al construir enlaces de paginación.

No se crea ni se cambia un Proyecto al asignar un nombre al trabajo.

## Apartados y exportaciones

Se presentan nombres junto a los códigos en los selectores, comparación y vistas relacionadas con clientes, proyectos, presupuestos y costos.

Las nuevas exportaciones PDF, PNG, Excel e impresión incluyen el nombre del trabajo. Los nombres de archivo siguen basándose en el código permanente (`OPT-0006.pdf`, `OPT-0006.xlsx`, `OPT-0006_tablero-1.png`) para no perder la referencia al renombrar. Los documentos previamente descargados no se modifican. Los nombres largos se ajustan o abrevian en los encabezados exportados para evitar desbordamientos.

El nombre se procesa como texto: se escapa al mostrar HTML, se guarda mediante el ORM y en Excel se fuerza el tipo de texto para evitar interpretar un nombre que comience con `=` como fórmula. El formulario específico exige autenticación, protección CSRF, método GET/POST y propiedad del registro. El destino de regreso se limita a resultado o historial.

Se ajustaron los selectores del tutorial de piezas para que el nuevo campo del nombre del trabajo no sea confundido con el nombre de una pieza.

## Datos y migración

`0004_nombre_optimizacion` añade `Optimizacion.nombre`, un campo de texto opcional con valor inicial vacío. Se aplicó a la base local y los registros anteriores conservan sus claves y datos. Se creó una copia previa de SQLite fuera del repositorio:

`C:/Users/Rick/.codex/visualizations/2026/10/03/01a0ff1d-7895-7aa3-a612-5ad3ee1d9398/review-qa/antes-nombres.sqlite3`

En otra instalación se debe ejecutar `python manage.py migrate` desde `cut/`, como parte de la actualización habitual. No se debe publicar la base SQLite ni los PDF de prueba junto con el código.

## Verificación

- **162 pruebas correctas** en base de datos y archivos de prueba independientes.
- Diez pruebas nuevas: creación con/sin nombre; normalización; cambio sin recalcular ni alterar otros campos; quitar nombre; límite de longitud; propiedad y CSRF; carga en edición/duplicación; búsqueda por nombre/pieza/código; escape HTML; Excel como texto; edición que conserva el código.
- Cambio y búsqueda del nombre comprobados en el navegador con un usuario de prueba. Revisión visual de PDF y PNG con nombre y código.
- 55 plantillas compiladas, `manage.py check` correcto y migraciones sin cambios adicionales pendientes.

La primera etapa de códigos permanentes y esta segunda etapa se incluyen en el mismo commit, con publicación autorizada por el usuario.
