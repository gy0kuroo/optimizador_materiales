# Cambios visuales: inicio de sesión

Estado: aprobado visualmente por el usuario e incluido en el bloque de mejora visual de login, registro e inicio.

## Cambio

Se unifica Barlow para títulos y texto general; se conservan números y contenido técnico en JetBrains Mono donde ya se utilizaban. Se retira la carga de Barlow Condensed y se cargan los pesos necesarios. El cambio tipográfico alcanza las pantallas que usan los tokens comunes.

El login combina panel de marca y formulario, con ilustración decorativa de tablero. El fondo exterior blanco usa una cuadrícula sutil que se adapta a oscuro. En móvil se apilan las columnas y se retira la ilustración para reducir altura.

Se aplica la paleta Deep Walnut (#4E2D01), Olive Wood (#7D6344), Ash Grey (#B7B8AB), Full Spectrum Blue (#4558E7) y True Cobalt (#1E287B), con tonos derivados para superficies y texto. La barra superior se omite en login para evitar repetir la marca.

Se conservan formulario Django, POST, CSRF, errores y enlaces a registro y recuperación. Los estilos están en login-redesign.css; el CSS antiguo sigue disponible para las pantallas aún no renovadas.

## Validación

GET y POST vacío de login correctos, CSRF y errores presentes. El usuario revisó y aprobó la apariencia del login. La comprobación exhaustiva de móvil, oscuro y teclado no se realizó en navegador.

Consulta [el resumen del bloque](CAMBIOS_MEJORA_VISUAL.md) para las pruebas generales y el alcance compartido.
