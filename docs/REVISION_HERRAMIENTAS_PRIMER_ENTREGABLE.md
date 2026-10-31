# Revisión de herramientas opcionales — 31/10/2026

## Objetivo y alcance
Revisión de Materiales, Clientes, Proyectos, Presupuestos, Plantillas, Costos, Comparación y Estadísticas para el primer entregable. Se conserva la paleta, tipografía, permisos y selección personalizada del menú. No se modifican el algoritmo, el esquema de datos ni las migraciones. No se publica ni despliega este bloque automáticamente.

## Cambios implementados

| Herramienta | Resultado de la revisión y cambios |
| --- | --- |
| Materiales | Se rechazan tableros fuera de 10–300 cm por lado, con conversión desde la unidad elegida. Se conservan precio opcional y biblioteca personal/sistema. |
| Plantillas | Editor por filas con nombre, dimensiones y cantidad; agregar/eliminar, etiquetas de unidad, máximo 20 tipos y 100 unidades por tipo. Validación servidor de finitud, nombres, dimensiones 0,1–300 cm por pieza y encaje individual según rotación. Tablero 10–300 cm; sierra 0–10 mm. Las plantillas antiguas se validan antes de cargarse y las incompatibles abren un formulario de corrección. El formato antiguo sin nombre sigue admitido. La biblioteca muestra dimensiones reales en cm. |
| Clientes | Duplicados del mismo propietario devuelven un error de formulario en lugar de fallar al guardar. Usuarios distintos pueden conservar clientes del mismo nombre. |
| Proyectos | Finalización posterior o igual al inicio; formularios conservan selecciones al fallar; agregar planes no los extrae silenciosamente de otro proyecto; identificadores inválidos se rechazan; acciones de eliminación se comprueban. Guardados compuestos dentro de transacciones. |
| Presupuestos | Importes no negativos y total dentro del campo monetario; elegir cliente existente y escribir uno nuevo simultáneamente produce un aviso; editar no precarga la alternativa con el cliente existente. Selecciones conservadas y reutilización de planes consistente al crear/editar. Guardados compuestos y adiciones dentro de transacciones. Se explica precio único por tablero y alcance de cotización. |
| Costos | Se explica que son estimaciones de material/mano de obra, no pagos. Los registros sin precio quedan fuera. Fechas inválidas o invertidas muestran avisos y no presentan el historial completo como si estuviera filtrado. |
| Comparación | Consultar no recalcula el algoritmo ni escribe en el historial. Resultados incompletos piden regenerar el plan. Planes con piezas/unidades distintas muestran advertencia: sus diferencias no demuestran cuál es mejor para el mismo trabajo. |
| Estadísticas | Se conservan los gráficos existentes, el aislamiento por usuario y la explicación del promedio por optimización. Períodos desconocidos se normalizan a todo el historial, también en exportaciones. No se añaden gráficos sin una pregunta concreta que responder. |

## Plantillas: uso y compatibilidad
1. Elegir unidad y medidas del tablero.
2. Añadir cada tipo de pieza en su fila, sin escribir comas ni código.
3. Guardar. El servidor valida también solicitudes manipuladas.
4. Cargar la plantilla para preparar un corte; guardar una plantilla no ejecuta la optimización.

Cambiar la unidad cambia la interpretación de los números, como en el formulario principal; no convierte automáticamente los valores escritos. El encaje se comprueba por pieza, no promete que todas entren en un único tablero. La sierra siempre se escribe en mm y se conserva internamente en cm. Sin JavaScript permanece el editor de texto compatible; los datos antiguos mal formados se muestran en él para corregirlos.

## Propuesta para el primer entregable

| Herramienta | Recomendación |
| --- | --- |
| Materiales y Plantillas | Incluir como opcionales prioritarias: apoyan directamente la preparación y repetición del corte. |
| Clientes y Proyectos | Incluir como organización opcional; no exigirlos para optimizar. |
| Presupuestos y Costos | Incluir como estimaciones opcionales, con sus límites visibles; no presentarlos como contabilidad, facturación ni registro de pagos. |
| Comparación y Estadísticas | Incluir como análisis opcional cuando existan suficientes resultados guardados; no asignar un ganador automático entre trabajos distintos. |

No se han retirado herramientas ni alterado las preferencias guardadas. La aprobación final del entregable requiere revisión del usuario/evaluadora.

## Verificación y límites
- Suite local aislada de Supabase: 214 pruebas Django aprobadas con los cambios finales. Comprobación de sintaxis JavaScript y `git diff --check` sin errores.
- Casos nuevos: límites en distintas unidades, cantidades/tipos, encaje con/sin rotación, plantilla antigua inválida, duplicados por usuario, fechas de proyecto, propiedad de asociaciones, presupuestos negativos/cliente ambiguo y comparación sin escritura.
- Navegador local sobre copia temporal: crear y guardar plantilla con dos filas; comprobación visual del formulario.
- No se han realizado pruebas de carga concurrente, pruebas de usuarios ni validación de estos cambios en Render. Las transacciones evitan guardados parciales ante errores, pero no constituyen por sí solas una garantía contra todas las carreras concurrentes.
- El RUT mantiene la validación de formato previa; no es un servicio de verificación de identidad. El presupuesto utiliza un solo precio para sus tableros: no calcula tarifas distintas por material ni impuestos.

## Revisión manual recomendada antes de publicar
Comprobar los ocho módulos con el menú personalizado, claro/oscuro y teléfono; crear/editar/cancelar; corregir un formulario inválido sin perder datos; cargar una plantilla antigua; revisar cotización y exportaciones con el mismo conjunto de planes. Esta revisión no sustituye la evaluación con usuarios.

## Ajuste de formato de RUT
Crear y editar clientes muestran el ejemplo `12345678-9`. Al guardar se eliminan puntos, se incorpora el guion antes del dígito verificador y se transforma `k` en `K`. Se admite el campo vacío y se rechazan formatos mal formados. Se mantiene la comprobación de formato: no se agregó verificación del dígito mediante módulo 11. Los registros existentes no se modifican masivamente; se normalizan al guardar nuevamente el formulario.

## Verificación del bloque para publicación
Suite completa final: **219 pruebas Django aprobadas** con RUT, navegación integrada y selectores de proyectos/presupuestos incluidos. Sintaxis de los cuatro archivos JavaScript modificados comprobada y `git diff --check` sin errores. La validación se realizó con base de pruebas aislada y archivos temporales, sin conexión a Supabase. Documentación complementaria: [navegación](CAMBIOS_NAVEGACION_INTEGRADA.md), [selección en proyectos](CAMBIOS_SELECCION_OPTIMIZACIONES_PROYECTO.md) y [selector de presupuestos](CAMBIOS_SELECTOR_PRESUPUESTOS.md).
