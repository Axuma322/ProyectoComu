"""Envía un mensaje corto con ACK de radio; no transfiere archivos."""
import sys
from ..radio import PAYLOAD_SIZE, configuration, describe, error_message, initialize, parser, shutdown


def main():
    cli = parser('Enviar un mensaje de prueba al receptor')
    cli.add_argument('--message', default='Hola desde ProyectoComu')
    args = cli.parse_args()
    radio = None
    try:
        payload = args.message.encode('utf-8')
        if not 1 <= len(payload) <= PAYLOAD_SIZE or b'\0' in payload:
            raise ValueError('El mensaje debe ocupar de 1 a 32 bytes UTF-8 y no contener NUL')
        config = configuration(args)
        print(describe(config), flush=True)
        radio = initialize(config)
        radio.open_tx_pipe(config['address'].encode('ascii'))
        radio.listen = False
        success = radio.write(payload.ljust(PAYLOAD_SIZE, b'\0'))
        if success:
            print('ACK recibido del radio remoto. Confirme el mensaje en la consola del receptor.')
            return 0
        radio.flush_tx()
        print('Sin ACK: revise que RX esté escuchando, la configuración de ambos radios, '
              'antenas, distancia y alimentación. No confirma que el mensaje se haya perdido.', file=sys.stderr)
        return 1
    except (ValueError, RuntimeError, OSError) as exc:
        print(error_message(exc), file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print('\nEnvío interrumpido.')
        return 130
    finally:
        shutdown(radio)


if __name__ == '__main__':
    sys.exit(main())
