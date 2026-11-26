"""Pruebas de integración sin hardware: códecs reales y canal de pruebas explícito."""
import io
import tempfile
import time
import unittest
from pathlib import Path
from PIL import Image
from .codecs import encode, decode, huffman_encode, huffman_decode
from .archivos import Receiver, send_file, unpack, START, DATA, FIN, ACK, packet, MAX_WIRE
from integracion.enlace import make_wire, reconstruct


class CodecTests(unittest.TestCase):
    def test_huffman_all_symbols_single_symbol_and_padding(self):
        for data in (b'x' * 99, bytes(range(256)) * 3, b'\0\xff' * 257, b'example'):
            with self.subTest(size=len(data)):
                self.assertEqual(huffman_decode(huffman_encode(data)), data)
        with self.assertRaises(ValueError):
            huffman_decode(huffman_encode(b'hello')[:-1])

    def test_actual_team_samples_lossless_byte_exact(self):
        samples = Path(__file__).parent / 'algoritmos/algoritmo_sin_perdidas'
        for path in sorted(samples.iterdir()):
            if path.suffix.lower() in {'.bmp', '.pgm'}:
                with self.subTest(file=path.name):
                    data, meta = encode(path, 'sin_perdidas')
                    self.assertEqual(decode(data, meta['modo']), path.read_bytes())

    def test_lossy_golden_bitstream_and_small_bmp_roundtrip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'small.bmp'
            image = Image.frombytes('L', (4, 1), bytes([0, 15, 16, 255]))
            image.save(path)
            data, meta = encode(path, 'con_perdidas', 4)
            self.assertEqual(data, b'QPG1\0\x04\0\x01\x04\0\x1f')
            with Image.open(io.BytesIO(decode(data, 'con_perdidas'))) as result:
                self.assertEqual(result.tobytes(), bytes([8, 8, 24, 248]))
            self.assertGreater(meta['mse_tx'], 0)
            with self.assertRaises(ValueError):
                decode(data[:-1], 'con_perdidas')

    def test_wire_reconstruct_validates_hash_and_publishes_real_image(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / 'file.bmp'
            Image.new('L', (19, 7), 42).save(path)
            for mode in ('sin_perdidas', 'con_perdidas'):
                data, meta = encode(path, mode, 5)
                result = reconstruct(make_wire(data, meta), root, 123, 0.4)
                self.assertTrue((root / 'recibidas' / result['nombre']).exists())
                self.assertTrue(result['metricas']['sha256_verificado'])
                self.assertIsNone(result['metricas']['ber'])
                meta['sha256_reconstruida'] = '0' * 64
                with self.assertRaises(ValueError):
                    reconstruct(make_wire(data, meta), root, 124, 0.4)

    def test_all_depths_partial_bytes_and_automatic_quality(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'odd.pgm'
            original = bytes((i * 37) % 256 for i in range(13 * 7))
            path.write_bytes(b'P5\n# cabecera variable del equipo\n13 7\n255\n' + original)
            for bits in range(1, 8):
                data, meta = encode(path, 'con_perdidas', bits)
                with Image.open(io.BytesIO(decode(data, 'con_perdidas'))) as result:
                    expected = bytes(((x >> (8-bits)) << (8-bits)) + (1 << (7-bits)) for x in original)
                    self.assertEqual(result.tobytes(), expected)
            data, meta = encode(path, 'automatico')
            self.assertTrue(meta['psnr_tx_db'] is None or meta['psnr_tx_db'] >= 25)
            self.assertIn(meta['modo'], ('sin_perdidas', 'con_perdidas'))
            self.assertEqual(len(data), meta['bytes_comprimidos'])


class TestChannel:
    """Solo para tests. No existe modo simulado en el proceso de radio real."""
    def __init__(self, receiver, drop=None, corrupt=False):
        self.receiver, self.drop, self.corrupt = receiver, drop, corrupt
        self.responses = []
        self.dropped = False

    def send(self, frame):
        kind, session, index, body = unpack(frame)
        if self.corrupt and kind == DATA and index == 0:
            frame = frame[:8] + bytes([frame[8] ^ 1]) + frame[9:]
        response = self.receiver.handle(frame)
        if kind == self.drop and not self.dropped:
            self.dropped = True
        elif response:
            self.responses.append(response)
        return True

    def receive(self, timeout):
        return self.responses.pop(0) if self.responses else None


class TransportTests(unittest.TestCase):
    def test_endpoint_sends_current_frame_despite_old_fifo_and_completion_flag(self):
        from .enlace import RadioEndpoint

        class OldCompletionRadio:
            # Modelo de una cola con una trama anterior y TX_DS pendiente.
            # Un write que da éxito sin vaciarla no prueba qué trama salió.
            def __init__(self):
                self.queue, self.delivered = [b'previous'], []
                self.completed = True
                self.get_arc = 2

            def stop_listening(self, address): pass
            def start_listening(self): pass
            def flush_tx(self): self.queue.clear()
            def clear_status_flags(self): self.completed = False

            def write(self, frame):
                self.queue.append(frame)
                if not self.completed:
                    self.delivered.append(self.queue.pop(0))
                    self.completed = True
                return True

        endpoint = RadioEndpoint.__new__(RadioEndpoint)
        endpoint.radio = OldCompletionRadio()
        endpoint.address = b'COMU1'
        endpoint.frames = endpoint.hardware_retries = 0
        self.assertTrue(endpoint.send(b'current'))
        self.assertTrue(endpoint.send(b'next'))
        self.assertEqual(endpoint.radio.delivered, [b'current', b'next'])
        self.assertEqual(endpoint.radio.queue, [])
        self.assertEqual(endpoint.frames, 2)
        self.assertEqual(endpoint.hardware_retries, 4)

    def test_lost_ack_at_each_phase_preserves_binary_and_exactly_once_finish(self):
        data = bytes(range(256)) * 8 + b'\0\0end\0'
        for lost in (None, START, DATA, FIN):
            with self.subTest(lost=lost):
                received = []
                channel = TestChannel(Receiver(lambda data, *_: received.append(data)), lost)
                diagnostics = {}
                result = send_file(channel, data, diagnostics=diagnostics)
                self.assertEqual(received, [data])
                self.assertTrue(result['confirmado_por_rx'])
                self.assertEqual(result['reintentos_aplicacion'], int(lost is not None))
                self.assertEqual(diagnostics['bytes_confirmados'], len(data))
                self.assertEqual(diagnostics['ack_hardware_ausentes'], 0)
                self.assertEqual(diagnostics['intentos_sin_ack_aplicacion'], int(lost is not None))
                self.assertEqual(diagnostics['tramas_aplicacion'], result['tramas_aplicacion'])

    def test_crc_failure_never_reports_success_or_publishes(self):
        received = []
        channel = TestChannel(Receiver(lambda data, *_: received.append(data)), corrupt=True)
        with self.assertRaises(RuntimeError):
            send_file(channel, b'payload' * 100)
        self.assertEqual(received, [])

    def test_timeout_and_oversized_start_are_bounded(self):
        class Offline:
            def send(self, frame): return False
            def receive(self, timeout): return None
        diagnostics = {}
        with self.assertRaises(TimeoutError):
            send_file(Offline(), b'image', retries=2, diagnostics=diagnostics)
        self.assertEqual(diagnostics['ack_hardware_ausentes'], 3)
        self.assertEqual(diagnostics['intentos_sin_ack_aplicacion'], 3)
        self.assertEqual(diagnostics['fragmentos_confirmados'], 0)
        import struct
        receiver = Receiver(lambda *_: self.fail('No debe completar'))
        answer = receiver.handle(packet(START, 4, body=struct.pack('>II', MAX_WIRE + 1, 0)))
        self.assertEqual(unpack(answer)[3][1], 1)
        self.assertIsNone(receiver.current)


if __name__ == '__main__':
    unittest.main()
