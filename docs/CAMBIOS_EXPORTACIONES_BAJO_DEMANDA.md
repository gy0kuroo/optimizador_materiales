# Historial y exportaciones bajo demanda

Fecha: 30 de octubre de 2026.

## Lógica acordada

El historial conserva parámetros, estadísticas y coordenadas de la distribución original en la base de datos. No se guardan PDF, PNG ni Excel nuevos como archivos permanentes del servidor, ni como contenido binario/base64 en la base de datos. Al descargar, se construye la representación en memoria y se entrega al navegador. El usuario decide dónde guardarla en su computador.

## Implementación

- Guardar una optimización persiste sus tableros y geometría JSON de forma transaccional. No genera un PDF ni escribe imágenes. Si falla el guardado, el resultado previo se conserva.
- Consultar un resultado ya calculado reconstruye las imágenes desde las coordenadas guardadas, sin ejecutar nuevamente el algoritmo. Las imágenes transitorias se mantienen solo en memoria durante la petición.
- El historial muestra su miniatura horizontal desde la geometría, aunque el campo legado de imagen esté vacío. El visor mantiene sus rutas y diseño.
- PDF y PNG se producen en memoria; Excel ya se producía así. La impresión utiliza la misma geometría guardada.
- Los PDF de presupuestos y resumen de desperdicio también se generan en memoria desde sus vistas, sin guardar una copia ni actualizar un campo con una ruta de archivo.
- Las vistas mantienen su filtrado por propietario. No se publican archivos de otros usuarios.

## Compatibilidad y límites

No se cambia el esquema ni se ejecutan migraciones. Los campos de archivo existentes permanecen como compatibilidad, vacíos en resultados nuevos. Los generadores PDF de bajo nivel aún aceptan su modalidad antigua de escritura si se invocan directamente sin buffer; las vistas de descarga pasan un buffer explícito.

Un resultado antiguo sin coordenadas puede leerse desde sus imágenes existentes. Si también faltan esas imágenes, se indica un error en vez de recalcular silenciosamente una distribución diferente. Los registros que aún no tienen ningún resultado persistido conservan la ruta de cálculo inicial. No se migra ni borra el histórico local en esta etapa, conforme a la decisión de comenzar producción con una base limpia.

No se garantiza que una descarga PDF tenga bytes idénticos entre versiones: se conserva la geometría; el formato de presentación y metadatos del documento pueden evolucionar. Generar bajo demanda consume CPU y memoria por petición; queda pendiente medirlo en Render/Linux. Esta implementación elimina la necesidad de un disco persistente para estas nuevas exportaciones, no los límites de recursos de la plataforma.

## Verificación

- Comprobación final antes de publicar: suite completa de 172 pruebas aprobadas, incluidas las pruebas de PDF de estadísticas y presupuestos. Se actualizaron los contratos antiguos que exigían guardar archivos.
- Verificados PDF y PNG por su firma de formato; Excel, impresión, API y miniaturas funcionan con los archivos nuevos ausentes.
- Pruebas bloquean el recálculo y las escrituras al almacenamiento al recuperar y exportar un resultado guardado. Se verifica que datos y archivos permanezcan iguales después de descargar, y que otra cuenta reciba 404.
- Se conservan pruebas de reversión transaccional en creación y edición cuando falla la base de datos.
- Se utilizaron una base de pruebas y una carpeta temporal; no se alteraron los datos locales reales. No se hizo una nueva revisión visual en navegador ni un despliegue.

Publicación autorizada el 30 de octubre de 2026; sin despliegue.
