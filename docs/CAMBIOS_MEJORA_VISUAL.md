# Mejora visual de login, registro e inicio

## Objetivo y resultado

Se renuevan las pantallas de acceso y creación de cuenta y se refina el panel principal para una lectura más clara y una apariencia coherente con la paleta del proyecto. El trabajo se revisó por secciones con el usuario antes de autorizar su publicación.

## Alcance

- [Login](CAMBIOS_VISUALES_LOGIN.md): composición, marca, fondo cuadriculado y tipografía.
- [Registro](CAMBIOS_VISUALES_REGISTRO.md): misma composición y requisitos de formulario visibles.
- [Inicio](CAMBIOS_VISUALES_PANEL.md): navegación, jerarquía, textos, contraste, tamaños y selectores.

La tipografía y la barra son compartidas. Los estilos específicos del panel y registro están aislados por clases. Historial conserva su nombre y rutas. No se modifica el algoritmo, los modelos ni las validaciones de cuenta.

## Validación y límites

Se ejecutó la suite de cutless.tests y usuarios.tests con base de pruebas y archivos temporales. Se comprobó que la base local y un PDF existente mantuvieron su hash. Resultado: 86 pruebas correctas y Django check sin problemas.

Login y registro se comprobaron por GET y POST vacío; las plantillas conservan CSRF y errores. El usuario aprobó las pantallas por revisión visual. No se realizó una auditoría integral de accesibilidad, navegación móvil o modo oscuro; esas revisiones siguen pendientes.

Los cambios previos en cut/db.sqlite3, PDFs locales y CAMBIOS_AREAS.md quedan fuera del commit.
