"""Endpoint pyRF24, configuración conservada de ~/prueba_radio.py."""
import time
from .radio import shutdown


class RadioEndpoint:
    """Adaptador síncrono: una escritura en vuelo y escucha tras cada envío.

    El bloqueo exclusivo pertenece al worker. Mantener FIFO/IRQ limpias evita
    confundir la finalización de una trama antigua con la escritura actual.
    """
    def __init__(self, config):
        import pyrf24 as rf
        self.radio = rf.RF24(config['ce_pin'], config['csn'], config['spi_speed'])
        self.address = config['address'].encode('ascii')
        if not self.radio.begin():
            raise RuntimeError('El módulo nRF24 no responde')
        self.radio.set_pa_level(rf.RF24_PA_MIN)
        self.radio.data_rate = getattr(rf, 'RF24_' + config['data_rate'])
        self.radio.channel = config['channel']
        self.radio.payload_size = 32
        self.radio.dynamic_payloads = False
        self.radio.crc_length = rf.RF24_CRC_16
        self.radio.set_auto_ack(True)
        self.radio.set_retries(5, 15)
        self.radio.flush_tx()
        self.radio.flush_rx()
        self.radio.clear_status_flags()
        self.radio.open_rx_pipe(1, self.address)
        self.radio.start_listening()
        self.frames = self.hardware_retries = 0

    def send(self, raw):
        """Devuelve ACK hardware; la confirmación de imagen es otra capa."""
        self.radio.stop_listening(self.address)
        # Solo hay una escritura bloqueante en curso. No reutilizar una trama
        # pendiente ni un TX_DS anterior como resultado de la trama nueva.
        self.radio.flush_tx()
        self.radio.clear_status_flags()
        success = self.radio.write(raw)
        self.frames += 1
        arc = self.radio.get_arc
        self.hardware_retries += arc() if callable(arc) else arc
        if not success:
            self.radio.flush_tx()
        self.radio.start_listening()
        return success

    def receive(self, timeout):
        """Espera local acotada sin bloquear indefinidamente el bucle de estados."""
        end = time.monotonic() + max(0, timeout)
        while time.monotonic() < end:
            if self.radio.available():
                return bytes(self.radio.read(32))
            time.sleep(0.001)
        return None

    def close(self):
        shutdown(self.radio)
