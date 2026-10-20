from django.test import SimpleTestCase
import matplotlib.pyplot as plt

from cutless.render import _dibujar_leyenda_tipos_piezas


class LeyendaPlanoTests(SimpleTestCase):
    def test_textos_largos_quedan_dentro_de_sus_celdas(self):
        tipos = [('WWWWWWWWWWWWWWWWWWWWWWWW', 40, 40),
                 ('Puerta superior del armario principal', 20, 30)]
        fig = plt.figure(figsize=(11.5, 9.8))
        try:
            ax = fig.add_axes([.51, .06, .45, .85])
            _dibujar_leyenda_tipos_piezas(
                ax, tipos, {k: i + 1 for i, k in enumerate(tipos)},
                {k: '#FF6B6B' for k in tipos}, 'cm', {k: 3 for k in tipos},
            )
            fig.canvas.draw()
            renderer = fig.canvas.get_renderer()
            tabla = ax.tables[0]
            for fila in range(1, 3):
                celda = tabla[fila, 1]
                texto = celda.get_text().get_window_extent(renderer)
                borde = celda.get_window_extent(renderer)
                self.assertGreaterEqual(texto.x0, borde.x0)
                self.assertLessEqual(texto.x1, borde.x1)
                self.assertGreaterEqual(texto.y0, borde.y0)
                self.assertLessEqual(texto.y1, borde.y1)
                self.assertGreaterEqual(celda.get_text().get_fontsize(), 12)
            self.assertEqual(tabla[1, 3].get_text().get_text(), '3')
            self.assertNotIn('…', tabla[2, 1].get_text().get_text())
        finally:
            plt.close(fig)

    def test_solo_incluye_tipos_presentes_en_el_tablero(self):
        tipos = [('Cajón', 20, 20), ('Puerta', 40, 40)]
        fig, ax = plt.subplots(figsize=(6, 9))
        try:
            _dibujar_leyenda_tipos_piezas(
                ax, tipos, {tipos[0]: 1, tipos[1]: 2},
                {k: '#45B7D1' for k in tipos}, 'mm', {tipos[1]: 18},
            )
            tabla = ax.tables[0]
            self.assertEqual(len(tabla.get_celld()), 8)
            self.assertEqual(tabla[1, 0].get_text().get_text(), '2')
            self.assertEqual(tabla[1, 2].get_text().get_text(), '400 × 400 mm')
            self.assertEqual(tabla[1, 3].get_text().get_text(), '18')
        finally:
            plt.close(fig)
