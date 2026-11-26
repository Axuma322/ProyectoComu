"""Patrones de LED sin GPIO: solo la tabla de tiempos de senales.patron."""
import unittest

from integracion.senales import patron, EXITO, ERROR_RAPIDO


def muestras(estado, modo=None, dip=None, dt=0.0, aviso_dt=None):
    # t recorre 4 s en pasos de 50 ms, como el hilo real
    return [patron(estado, modo, dip, i * 0.05, dt, aviso_dt) for i in range(80)]


class Patrones(unittest.TestCase):
    def test_esperando_es_un_latido_corto(self):
        verdes = [v for v, _, _ in muestras('esperando')]
        self.assertTrue(any(verdes))
        self.assertLess(sum(verdes), len(verdes) / 5)
        self.assertEqual(verdes, [v for v, _, _ in muestras('escuchando')])

    def test_transmitiendo_verde_fijo_y_codificando_rapido(self):
        self.assertTrue(all(v for v, _, _ in muestras('enviando')))
        self.assertTrue(all(v for v, _, _ in muestras('recibiendo')))
        rapido = [v for v, _, _ in muestras('codificando')]
        self.assertGreater(sum(rapido), 30)
        self.assertLess(sum(rapido), 50)

    def test_exito_destella_y_vuelve_al_latido(self):
        inicio = [patron('completado', None, None, 0, i * 0.05)[0] for i in range(int(EXITO / 0.05))]
        encendidas = sum(1 for a, b in zip([False] + inicio, inicio) if b and not a)
        self.assertEqual(encendidas, 3)
        despues = [patron('completado', None, None, i * 0.05, EXITO + 1)[0] for i in range(80)]
        self.assertLess(sum(despues), 10)
        self.assertFalse(any(r for _, _, r in muestras('completado')))

    def test_error_parpadea_y_luego_queda_fijo(self):
        rapido = [patron('error', None, None, 0, i * 0.05)[2] for i in range(40)]
        self.assertTrue(any(rapido) and not all(rapido))
        self.assertTrue(patron('error', None, None, 0, ERROR_RAPIDO + 1)[2])
        self.assertTrue(all(r for _, _, r in muestras('error_radio')))

    def test_azul_sigue_al_dip_mientras_espera(self):
        self.assertTrue(patron('esperando', None, {'modo': 'con_perdidas'}, 0, 0)[1])
        self.assertFalse(patron('esperando', 'con_perdidas', {'modo': 'sin_perdidas'}, 0, 0)[1])
        auto = [a for _, a, _ in muestras('esperando', dip={'modo': 'automatico'})]
        self.assertTrue(any(auto) and not all(auto))
        # Durante el envío manda el modo real del trabajo, no el DIP
        self.assertTrue(patron('enviando', 'con_perdidas', {'modo': 'sin_perdidas'}, 0, 0)[1])

    def test_rx_muestra_modo_recibido(self):
        self.assertTrue(patron('completado', 'con_perdidas', None, 0, 5)[1])
        self.assertFalse(patron('completado', 'sin_perdidas', None, 0, 5)[1])

    def test_aviso_sin_imagen_usa_el_rojo(self):
        rojos = [patron('esperando', None, None, 0, 0, i * 0.05)[2] for i in range(20)]
        self.assertTrue(any(rojos) and not all(rojos))
        self.assertFalse(patron('esperando', None, None, 0, 0, 2.0)[2])


if __name__ == '__main__':
    unittest.main()
