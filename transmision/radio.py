"""Configuración común de la prueba mínima. Backend pyRF24 SPIDEV."""
import argparse
import json
from pathlib import Path

DEFAULT_CONFIG = Path(__file__).with_name('config.json')
PAYLOAD_SIZE = 32


def parser(description):
    result = argparse.ArgumentParser(description=description)
    result.add_argument('--config', type=Path, default=DEFAULT_CONFIG)
    result.add_argument('--ce-pin', type=int, help='GPIO BCM conectado a CE')
    result.add_argument('--csn', type=int, choices=[0, 1], help='SPI0: 0=CE0, 1=CE1')
    result.add_argument('--spi-speed', type=int, help='Frecuencia SPI en Hz')
    result.add_argument('--channel', type=int, help='Canal RF, 0 a 125')
    result.add_argument('--data-rate', choices=['250KBPS', '1MBPS', '2MBPS'])
    result.add_argument('--address', help='Dirección de exactamente 5 caracteres ASCII')
    return result


def configuration(args):
    try:
        config = json.loads(args.config.read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        raise ValueError(f'No se pudo leer la configuración {args.config}: {exc}') from exc
    fields = {'ce_pin', 'csn', 'spi_speed', 'channel', 'data_rate', 'address'}
    if not isinstance(config, dict) or set(config) != fields:
        raise ValueError('La configuración debe contener: ' + ', '.join(sorted(fields)))
    for key in fields:
        override = getattr(args, key)
        if override is not None:
            config[key] = override
    for key, low, high in [('ce_pin', 0, 27), ('csn', 0, 1),
                           ('spi_speed', 1, 10000000), ('channel', 0, 125)]:
        if type(config[key]) is not int or not low <= config[key] <= high:
            raise ValueError(f'{key} debe ser un entero entre {low} y {high}')
    if config['ce_pin'] in {7, 8, 9, 10, 11}:
        raise ValueError('CE no debe compartir los pines reservados para SPI0 (BCM7..11)')
    if config['data_rate'] not in ('250KBPS', '1MBPS', '2MBPS'):
        raise ValueError('data_rate debe ser 250KBPS, 1MBPS o 2MBPS')
    try:
        address = config['address'].encode('ascii')
    except (AttributeError, UnicodeError) as exc:
        raise ValueError('address debe ser texto ASCII') from exc
    if len(address) != 5:
        raise ValueError('address debe tener exactamente 5 bytes ASCII')
    return config


def shutdown(radio):
    if radio is not None:
        try:
            radio.listen = False
            radio.power = False
        except Exception:
            pass  # No ocultar el error original ni impedir salir con Ctrl+C.


def initialize(config):
    try:
        import pyrf24
    except (ImportError, OSError) as exc:
        raise RuntimeError('No se pudo cargar pyrf24. Revise el entorno Python y la '
                           f'compatibilidad ARMv6 de la instalación: {exc}') from exc
    if pyrf24.RF24_DRIVER != 'SPIDEV':
        raise RuntimeError('Esta prueba requiere pyRF24 compilado con RF24_DRIVER=SPIDEV')
    device = Path(f'/dev/spidev0.{config["csn"]}')
    if not device.exists():
        raise RuntimeError(f'No existe {device}. Active SPI con raspi-config y reinicie.')
    radio = None
    try:
        radio = pyrf24.RF24(config['ce_pin'], config['csn'], config['spi_speed'])
        if not radio.begin() or not radio.is_chip_connected:
            raise RuntimeError('El radio no responde por SPI. Revise alimentación, GND, '
                               'orientación, CE, CSN, SCK, MOSI y MISO; no conecte 5 V al chip.')
        radio.listen = False
        if config['data_rate'] == '250KBPS' and not radio.is_plus_variant:
            raise RuntimeError('250 kbit/s requiere variante +; use 1MBPS hasta identificar el radio.')
        radio.channel = config['channel']
        radio.data_rate = getattr(pyrf24, 'RF24_' + config['data_rate'])
        if radio.channel != config['channel'] or radio.data_rate != getattr(pyrf24, 'RF24_' + config['data_rate']):
            raise RuntimeError('La configuración de canal o velocidad no coincide al leer el radio.')
        radio.set_pa_level(pyrf24.RF24_PA_LOW)
        radio.address_width = 5
        radio.dynamic_payloads = False
        radio.ack_payloads = False
        radio.payload_size = PAYLOAD_SIZE
        radio.crc_length = pyrf24.RF24_CRC_16
        radio.set_auto_ack(True)
        radio.set_retries(5, 5)  # 1500 us entre intentos, cinco reintentos hardware.
        for pipe in range(6):
            radio.close_rx_pipe(pipe)
        radio.flush_rx()
        radio.flush_tx()
        return radio
    except Exception:
        shutdown(radio)
        raise


def describe(config):
    return (f'CE=BCM{config["ce_pin"]}, CSN=/dev/spidev0.{config["csn"]}, '
            f'SPI={config["spi_speed"]} Hz, canal={config["channel"]}, '
            f'tasa={config["data_rate"]}, dirección={config["address"]}, '
            'carga=32 bytes, CRC=16 bits, auto-ACK, potencia LOW')


def error_message(exc):
    return (f'Error: {exc}\nRevise SPI, cableado y alimentación. Si el error es de permisos, '
            'revise /dev/spidev* y acceso GPIO; consulte transmision/README.md.')
