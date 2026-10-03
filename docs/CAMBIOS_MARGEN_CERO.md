# CutLess: margen de corte cero, tercera etapa

Fecha: 3 de octubre de 2026.

## Problema resuelto

El formulario acepta cero como margen de corte, pero varias rutas usaban `valor or 3` o `valor or 0.3`. En Python, cero es falso y se sustituía por 3 mm (0,3 cm en los cálculos internos).

Esto podía aumentar el número de tableros y producir resultados diferentes al regenerar o imprimir. Cuatro piezas de 50 × 50 cm en un tablero de 100 × 100 cm usan un tablero con margen cero; con 3 mm, el motor actual utiliza cuatro tableros.

## Comportamiento actual

El predeterminado se aplica únicamente cuando el dato es `None`; cero se conserva como valor válido.

| Entrada del formulario | Margen interno |
| --- | --- |
| `0` mm | `0` cm |
| Campo vacío | `0.3` cm, equivalentes a 3 mm |
| `1` mm | `0.1` cm |
| `3` mm | `0.3` cm |

Al regenerar desde un objeto, un atributo ausente o con valor `None` conserva el predeterminado de 0,3 cm. Los márgenes positivos mantienen su valor.

La corrección cubre creación, edición, regeneración de gráficos, estadísticas recalculadas para exportación, impresión del plan y cálculo de tableros para comparar optimizaciones. La duplicación ya convertía la cadena `'0'` correctamente y no necesitó cambios.

## Archivos afectados

- `cut/cutless/views/optimization.py`: creación y edición distinguen cero de campo vacío.
- `cut/cutless/services/optimization.py`: regeneración de gráficos.
- `cut/cutless/render.py`: regeneración de estadísticas.
- `cut/cutless/views/exports.py`: plan de impresión.
- `cut/cutless/views/analytics.py`: cálculo de tableros para comparar optimizaciones.
- `cut/cutless/tests/test_margen_cero.py`: ocho pruebas nuevas.
- `docs/CAMBIOS_SEGURIDAD.md` y `docs/CAMBIOS_JSON_SEGURO.md`: referencias actualizadas.
- `docs/CAMBIOS_MARGEN_CERO.md`: documentación de esta etapa.

No requiere migraciones, nuevas dependencias ni cambios de configuración. No modifica el algoritmo de empaquetado.

## Validación

**48 pruebas aprobadas** en la suite completa de `cutless.tests` y `usuarios.tests`. Django no detectó problemas de configuración.

Las ocho pruebas nuevas verifican:

1. Crear con cero guarda el margen y un tablero, con aprovechamiento del 100 %.
2. Editar de 0,3 cm a cero guarda un tablero.
3. Crear con campo vacío y márgenes positivos conserva los valores previstos.
4. Editar con campo vacío usa el predeterminado de 3 mm.
5. Regenerar gráficos con cero coloca las cuatro piezas en un tablero.
6. Regenerar estadísticas con cero produce un tablero sin desperdicio.
7. Imprimir con cero produce un plan de un tablero.
8. Un margen ausente o `None` usa el predeterminado al regenerar gráficos y estadísticas.

Las pruebas utilizaron una base de datos de pruebas y una carpeta temporal para `MEDIA_ROOT` y la caché de Matplotlib. La ejecución inicial fue bloqueada por permisos de escritura; al repetir con los permisos necesarios, todas pasaron. Se verificó mediante SHA-256 que `cut/db.sqlite3` y `cut/media/pdfs/optimizacion_1.pdf` permanecieran intactos.

Para reproducir la suite con archivos aislados, desde la raíz del repositorio en PowerShell:

```powershell
@'
import os, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path('cut').resolve()))
os.environ['DJANGO_SETTINGS_MODULE'] = 'cutless_project.settings'
with tempfile.TemporaryDirectory(prefix='cutless-tests-') as tmp:
    os.environ['MPLCONFIGDIR'] = str(Path(tmp) / 'matplotlib')
    from django.conf import settings
    settings.MEDIA_ROOT = str(Path(tmp) / 'media')
    import django
    django.setup()
    from django.test.utils import get_runner
    failures = get_runner(settings)(verbosity=1).run_tests(['cutless.tests', 'usuarios.tests'])
raise SystemExit(bool(failures))
'@ | python -B -
```

No se realizó una validación visual en navegador. La comparación de optimizaciones no tiene una nueva prueba de integración específica; su lectura del margen se corrigió junto con las demás rutas.

## Resultados anteriores

Esta corrección no repara automáticamente registros anteriores. Si un cero ya fue guardado como 0,3 cm, no puede distinguirse de un margen de 3 mm elegido intencionadamente. Es necesario editar esas optimizaciones con margen cero para recalcularlas.

Los resultados persistidos siguen reutilizándose mientras sus archivos estén disponibles. Editar la optimización permite generar nuevamente el resultado con los parámetros deseados.

## Publicación en GitHub

```powershell
git add cut/cutless/views/optimization.py cut/cutless/services/optimization.py cut/cutless/render.py cut/cutless/views/exports.py cut/cutless/views/analytics.py cut/cutless/tests/test_margen_cero.py docs/CAMBIOS_SEGURIDAD.md docs/CAMBIOS_JSON_SEGURO.md docs/CAMBIOS_MARGEN_CERO.md
git diff --cached --check
git diff --cached --stat
git commit -m "fix: respetar margen de corte cero"
git push origin main
```

La base de datos y los archivos generados locales quedan fuera de este bloque.

## Siguiente prioridad

Corregir las conversiones de áreas que emplean factores lineales previamente redondeados.
