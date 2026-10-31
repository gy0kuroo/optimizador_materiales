# Navegación lateral integrada — 31/10/2026

- Inicio e Historial pasan a enlaces alineados a la izquierda, sin apariencia de botones de formulario.
- Gestión, Análisis y Cuenta se despliegan dentro de la barra mediante `details`/`summary`, con soporte nativo de teclado y sin menús flotantes. Se conserva la navegación plegable exterior de móvil y su bloqueo de desplazamiento.
- Opciones con sangría y guía vertical discreta; solo el destino activo tiene fondo destacado de la paleta cobre. El grupo correspondiente se abre desde el HTML inicial, incluso al crear o editar registros.
- Se conservan destinos, permisos y preferencias de herramientas. Ayuda y Cuenta mantienen su posición en la zona inferior; si las opciones exceden el alto, la barra conserva desplazamiento.
- Estado de navegación incluido en `initial_assets`, ya registrada. Se eliminó la biblioteca nueva `navigation` porque un servidor abierto no la descubría y producía `TemplateSyntaxError` al renderizar formularios.

Validación: 214 pruebas Django aprobadas, incluida creación/edición de plantillas; apertura de Gestión y navegación a Plantillas comprobadas en navegador local con copia temporal y modo oscuro. No se ejecutaron commits, push ni despliegues. La revisión visual en teléfono y con usuarios sigue pendiente.
