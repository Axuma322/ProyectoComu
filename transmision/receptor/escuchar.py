"""Escucha indefinidamente hasta Ctrl+C y muestra las cargas recibidas."""
import sys
import time
from ..radio import PAYLOAD_SIZE, configuration, describe, error_message, initialize, parser, shutdown


def main():
    args = parser('Escuchar mensajes de prueba hasta Ctrl+C').parse_args()
    radio = None
    try:
        config = configuration(args)
        print(describe(config), flush=True)
        radio = initialize(config)
        radio.open_rx_pipe(1, config['address'].encode('ascii'))
        radio.listen = True
        print('Escuchando. Termine con Ctrl+C.', flush=True)
        while True:
            if radio.available():
                raw = bytes(radio.read(PAYLOAD_SIZE))
                if len(raw) != PAYLOAD_SIZE:
                    raise RuntimeError('Lectura de radio incompleta; se esperaban 32 bytes')
                message = raw.rstrip(b'\0')
                print(f'RX {len(message)} bytes: {message.decode("utf-8", errors="backslashreplace")!r} '
                      f'[hex={message.hex()}]', flush=True)
            else:
                time.sleep(0.01)
    except KeyboardInterrupt:
        print('\nEscucha finalizada.')
        return 0
    except (ValueError, RuntimeError, OSError) as exc:
        print(error_message(exc), file=sys.stderr)
        return 1
    finally:
        shutdown(radio)


if __name__ == '__main__':
    sys.exit(main())
