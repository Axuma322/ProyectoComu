"""Pruebas de lógica con radio simulado; no sustituyen la prueba física."""
from contextlib import redirect_stdout, redirect_stderr
import io
import types
import unittest
from unittest.mock import MagicMock, patch
from . import radio
from .transmisor import enviar
from .receptor import escuchar


class PruebaMinima(unittest.TestCase):
    def config(self, *args):
        return radio.configuration(radio.parser('prueba').parse_args(args))

    def test_config_y_opciones(self):
        self.assertEqual(self.config()['ce_pin'], 22)
        config = self.config('--channel', '45', '--address', 'OTRO1', '--csn', '1')
        self.assertEqual((config['channel'], config['address'], config['csn']), (45, 'OTRO1', 1))
        for args in [('--channel', '126'), ('--ce-pin', '8'), ('--address', 'larga1')]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                self.config(*args)

    def test_spi_no_responde_y_apagado(self):
        device = MagicMock()
        device.begin.return_value = False
        lib = types.SimpleNamespace(RF24_DRIVER='SPIDEV', RF24=MagicMock(return_value=device))
        with patch.dict('sys.modules', pyrf24=lib), patch.object(radio.Path, 'exists', return_value=True):
            with self.assertRaisesRegex(RuntimeError, 'no responde'):
                radio.initialize(self.config())
        self.assertFalse(device.power)

    def test_configuracion_explicita(self):
        device = MagicMock(is_chip_connected=True, is_plus_variant=False)
        lib = types.SimpleNamespace(RF24_DRIVER='SPIDEV', RF24=MagicMock(return_value=device),
                                   RF24_1MBPS=1, RF24_PA_LOW=1, RF24_CRC_16=2)
        with patch.dict('sys.modules', pyrf24=lib), patch.object(radio.Path, 'exists', return_value=True):
            self.assertIs(radio.initialize(self.config()), device)
            self.assertEqual(device.payload_size, 32)
            self.assertEqual(device.crc_length, 2)
            device.set_auto_ack.assert_called_once_with(True)
            device.set_retries.assert_called_once_with(5, 5)
            with self.assertRaisesRegex(RuntimeError, 'variante'):
                radio.initialize(self.config('--data-rate', '250KBPS'))

    def test_tx_ack_y_sin_ack(self):
        for ack in (True, False):
            device = MagicMock()
            device.write.return_value = ack
            with patch('sys.argv', ['enviar', '--message', 'Hola K3']), \
                 patch.object(enviar, 'initialize', return_value=device), \
                 redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(enviar.main(), 0 if ack else 1)
            device.write.assert_called_once_with(b'Hola K3' + b'\0' * 25)
            self.assertFalse(device.power)

    def test_mensaje_largo_no_inicializa(self):
        with patch('sys.argv', ['enviar', '--message', 'á' * 17]), \
             patch.object(enviar, 'initialize') as init, redirect_stderr(io.StringIO()):
            self.assertEqual(enviar.main(), 1)
        init.assert_not_called()

    def test_rx_muestra_y_termina(self):
        device = MagicMock()
        device.available.side_effect = [True, KeyboardInterrupt()]
        device.read.return_value = b'Hola K3' + b'\0' * 25
        output = io.StringIO()
        with patch('sys.argv', ['escuchar']), patch.object(escuchar, 'initialize', return_value=device), \
             redirect_stdout(output):
            self.assertEqual(escuchar.main(), 0)
        self.assertIn('Hola K3', output.getvalue())
        self.assertFalse(device.power)


if __name__ == '__main__':
    unittest.main()
