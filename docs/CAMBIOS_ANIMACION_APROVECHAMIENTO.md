# Animación y escala de color del aprovechamiento

Fecha: 25 de octubre de 2026.

## Comportamiento

Se conserva el gráfico circular existente. Al cambiar de tablero, su relleno se desplaza desde el porcentaje anterior hasta el nuevo durante 650 milisegundos, con desaceleración al terminar. Por ejemplo, de 90 % a 60 % el anillo retrocede; no vuelve a empezar desde cero.

El color se calcula continuamente a partir del porcentaje mostrado: rojo en 0 %, ocre en 50 % y verde en 100 %, pasando por tonos intermedios. Esta escala describe el aprovechamiento; no cambia el significado de botones ni el color de las piezas del plano. No establece nuevos umbrales de aprobación del cálculo.

Se aplica a:

- El gráfico por tablero en el resultado.
- El gráfico del visor ampliado del resultado.
- El gráfico del visor de tableros del historial.
- El color del gráfico de aprovechamiento total. Su valor permanece independiente del tablero seleccionado.

La primera presentación muestra directamente el porcentaje real. Los cambios posteriores se animan desde el último valor visible, incluso al navegar rápidamente. Se cancelan las animaciones anteriores para evitar saltos. Las preferencias de movimiento reducido se respetan y muestran el destino inmediatamente, también si se activan durante una transición.

El número y la descripción accesible conservan el porcentaje final real durante la transición. El significado no depende exclusivamente del color. No se modifican medidas, distribución, cálculos, datos guardados ni exportaciones. No se agregan controles.

## Implementación

`utilization.js` comparte el comportamiento entre los tres puntos de navegación. Cada visor mantiene su propio estado. El atributo `data-utilization` contiene el dato calculado por Django; solo el trazo y el color del SVG se interpolan mediante `requestAnimationFrame`. `pathLength="100"` normaliza el recorrido circular a la escala porcentual.

## Validación

Cuatro pruebas automatizadas de JavaScript aprobadas:

1. Transición 90 → 60 con valor intermedio y destino exacto.
2. Navegación rápida desde el valor visible y cancelación de la animación anterior.
3. Escala de color, límites entre 0 y 100 y movimiento reducido.
4. Independencia entre aprovechamiento total y aprovechamiento por tablero.

Comando desde la raíz del repositorio:

```powershell
node cut/cutless/tests/js/utilization.test.cjs
```

Se comprobó además la sintaxis de los scripts de navegación, la compilación de las tres plantillas afectadas y la ausencia de errores de espacios en el diff del código. Pendiente la evaluación visual del usuario en su navegador.

Mejora visual preparada para publicación con sus pruebas y documentación. Los datos locales y los pendientes de otras tareas quedan fuera del commit.
