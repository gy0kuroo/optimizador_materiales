# Mensajes y ayuda progresiva de login y registro

Fecha: 27 de octubre de 2026.

## Registro

Los errores aparecen junto al campo, con una señal de advertencia, texto concreto y borde rojo adaptado al tema. Se reformulan los mensajes de campos obligatorios, correo inválido, usuario ocupado, contraseñas diferentes y los validadores de contraseña existentes. Los códigos de validación se conservan.

La ayuda se revela al enfocar cada campo. La contraseña incluye una guía que comprueba la longitud mínima configurada y, si está habilitado el validador correspondiente, que no contenga solo números. La coincidencia se informa después de revisar la confirmación. Se utilizan marcas y texto, además del color.

Las comprobaciones locales no verifican disponibilidad del usuario, contraseñas comunes ni similitud con los datos de cuenta. Se explica que estas verificaciones se realizan en el servidor; no se presenta una contraseña como definitivamente válida por cumplir la guía local.

Los errores locales se muestran al salir del campo o enviar el formulario. Mientras se corrige un campo ya revisado, el mensaje se actualiza sin repetir el mismo anuncio a cada pulsación. Un envío local inválido enfoca el resumen para facilitar su localización. Los campos nuevos no aparecen marcados como erróneos al abrir la página.

Si el servidor rechaza el registro, se conservan usuario y correo y se dejan vacías las contraseñas, como ya hacía Django. Sin JavaScript, las ayudas permanecen visibles y el servidor valida el formulario completo.

## Login y confirmación del registro

Un intento fallido muestra: «No pudimos iniciar sesión. Revisa tu usuario y contraseña», con una indicación de que puede intentarse de nuevo o recuperarse la contraseña. No se distingue públicamente entre usuario inexistente y contraseña equivocada.

Tras crear una cuenta aparece «Tu cuenta está lista. Ahora inicia sesión» dentro del panel de login, sin duplicar el aviso por encima del formulario. El aviso integrado no desaparece automáticamente. La cuenta no inicia sesión por el hecho de registrarse; se conserva el flujo anterior.

## Integración y accesibilidad

- Los formularios de Django mantienen sus validadores y guardado. Se añade una presentación común de errores y un formulario de acceso con mensajes personalizados.
- La plantilla compartida de campos vincula ayuda y errores mediante `aria-describedby`; los campos inválidos indican `aria-invalid`. Los mensajes locales utilizan anuncios discretos con `aria-live="polite"`.
- `auth-feedback.js` presenta la ayuda y las comprobaciones locales, sin peticiones adicionales para consultar usuarios. Los mensajes se construyen con `textContent`.
- `auth-feedback.css` usa los tokens de la paleta existente. Las transiciones breves se desactivan cuando se prefiere movimiento reducido. No se introducen popups, medidores de seguridad arbitrarios ni cambios de tipografía.
- La plantilla base incorpora un bloque de mensajes que el login puede reubicar. Los avisos del resto de las pantallas mantienen su ubicación.

## Verificación

La suite completa pasó **175 pruebas**, incluidas seis regresiones nuevas de estos formularios. Tras ajustar la guía a los validadores configurados se repitieron esas seis, todas aprobadas.

Se comprueba: errores accesibles y datos conservados, ausencia de contraseñas en los valores HTML, validadores de contraseña activos, usuario duplicado, confirmación única del registro sin autenticar automáticamente, mensaje de acceso uniforme y guía adaptada a otra longitud mínima de servidor.

En navegador, sobre una copia temporal de la base de datos:

- Correo inválido, contraseña corta y confirmación diferente.
- Cambio de los requisitos y aviso de coincidencia al corregir los datos.
- Registro correcto de una cuenta de prueba y confirmación dentro del login.
- Acceso fallido y posterior acceso correcto de esa cuenta.
- Mensajes y bordes visibles en claro y oscuro. En oscuro la tinta y el borde de error computados son `rgb(224, 107, 121)`; en claro, el borde es `rgb(139, 38, 53)`.

La sintaxis del JavaScript y el diff no presentan incidencias. Los datos y preferencias reales del usuario no se modificaron. El servidor temporal y la pestaña de revisión se cerraron al terminar.

Mejora aprobada para publicación con sus pruebas y documentación. Los datos locales y pendientes de otras tareas quedan fuera del commit.
