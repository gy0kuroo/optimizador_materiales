# Ayuda: presentación y recorrido contextual

Fecha: 6 de octubre de 2026. Mejora revisada y aprobada por el usuario para publicación.

## Problemas corregidos

Los cuadros de Intro.js conservaban un ancho reducido y letras pequeñas. El título usaba café incluso en modo oscuro, mientras el fondo seguía siendo blanco. La guía general no reconocía la ruta actual del historial y algunos textos describían botones y pestañas anteriores.

## Cambios

- Hoja compartida `help-redesign.css`, cargada después de los estilos de cada pantalla: cuadros de hasta 440 px, adaptados al ancho y alto de la ventana, texto de 1.125 rem, títulos de 1.25 rem y botones de al menos 48 px. Respeta el tamaño de letra elegido en Perfil.
- Fondos, texto, bordes y flechas utilizan las variables de la paleta en ambos temas. El modal de bienvenida utiliza la misma presentación.
- Controles Anterior, Siguiente, Finalizar y cierre con etiqueta accesible; foco visible y respeto por movimiento reducido. Se eliminan los puntos pequeños de navegación. Cerrar requiere el botón o Escape, evitando salidas accidentales al pulsar fuera.
- Ayuda identifica la pantalla mediante el nombre de la ruta Django y reutiliza su recorrido específico, incluidos Historial, Resultado, Perfil, Configuración y las pantallas de gestión.
- Los pasos con controles inexistentes u ocultos se omiten. Si no hay controles disponibles se muestra una explicación sin resaltar todo el documento. Abrir otra guía cierra la anterior.
- Inicio utiliza los nombres actuales de los botones; Perfil explica Preferencias y Cuenta y contraseña; Resultado explica correctamente el detalle por tablero y señala sus acciones actuales.
- Cerrar el recorrido de Inicio ya no lo marca como completado. Finalizarlo sí conserva ese registro. El botón Omitir del mensaje de bienvenida conserva su comportamiento previo.

## Validación

- `python -B cut/manage.py check`: sin incidencias.
- Ejecución del JavaScript de la plantilla en Node con un DOM simulado: seis comprobaciones de ruta del historial, filtrado de controles, alternativa sin controles, finalización y textos de Perfil y Resultado.
- El usuario confirmó que Ayuda funciona correctamente en su navegador. No se ha realizado una comprobación automatizada de todas las combinaciones de tema, tamaño de letra y ancho de ventana.

No se modifican datos del usuario, permisos ni cálculos. No requiere migración.
