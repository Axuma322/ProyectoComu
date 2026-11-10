"""Diagnóstico local de inicialización; no transmite mensajes de prueba."""
import sys
from .radio import configuration, describe, error_message, initialize, parser, shutdown


def main():
    args = parser('Diagnosticar el radio conectado por SPI').parse_args()
    radio = None
    try:
        config = configuration(args)
        print(describe(config), flush=True)
        radio = initialize(config)
        print('Inicialización y lectura SPI correctas. Esto no comprueba el enlace inalámbrico.')
        print(f'El controlador identifica variante +: {radio.is_plus_variant}; '
              'no identifica el módulo, amplificador ni su alimentación.')
        radio.print_pretty_details()
        return 0
    except (ValueError, RuntimeError, OSError) as exc:
        print(error_message(exc), file=sys.stderr)
        return 1
    finally:
        shutdown(radio)


if __name__ == '__main__':
    sys.exit(main())
