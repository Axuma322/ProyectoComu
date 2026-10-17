"""Escenarios analiticos propios; sin radio, dependencias ni resultados experimentales."""
import math


def fspl_db(f_mhz, d_m):
    """UIT-R P.525: 20 log10(4 pi d f / c), unidades SI."""
    if f_mhz <= 0 or d_m <= 0:
        raise ValueError("Frecuencia y distancia deben ser positivas")
    return 20 * math.log10(4 * math.pi * d_m * f_mhz * 1e6 / 299792458)


def escenario_capacidad(n_bytes=76800, data_bytes=24, header_bytes=8,
                        rate=1000000, host_s=0.002):
    """Carga fija 32 B, direccion 5 B, CRC 2 B, ACK vacio, sin reintentos.

    2 cambios de modo de 130 us por intercambio como supuesto conservador.
    No modela START/META/FIN, ACK de bloque, ARD ni procesamiento de imagen.
    """
    n = math.ceil(n_bytes / data_bytes)
    rf_header_bits = 8 + 40 + 9 + 16
    data_packet_bits = rf_header_bits + 8 * (data_bytes + header_bytes)
    ack_bits = rf_header_bits
    air_s = n * (data_packet_bits + ack_bits) / rate
    exchange_s = air_s + n * (2 * 130e-6 + host_s)
    tx_rf_bytes_equiv = n * (data_packet_bits + ack_bits) / 8
    overhead = 1 - n_bytes / tx_rf_bytes_equiv
    return n, air_s, exchange_s, tx_rf_bytes_equiv, overhead


def main():
    print('HIPOTESIS: f=2440 MHz; Pt=0 dBm; Gt=Gr=0 dBi; perdidas extra=3 dB')
    for d in (30, 100):
        loss = fspl_db(2440, d)
        rx = 0 + 0 + 0 - loss - 3
        print(f'd={d} m: FSPL={loss:.3f} dB; Pr={rx:.3f} dBm')
        for rate, sensitivity in ((250000, -94), (1000000, -85), (2000000, -82)):
            print(f'  {rate} bit/s: margen={rx - sensitivity:.3f} dB')
    print('CAPACIDAD: raster 320x240x8 bits, NO incluye cabecera BMP/PGM')
    print(f'Raster={320 * 240} bytes; umbral bruto raster/60={320 * 240 / 60:.1f} B/s')
    for rate in (250000, 1000000, 2000000):
        for host_s in (0, 0.002, 0.010):
            n, air, exchange, traffic, overhead = escenario_capacidad(rate=rate, host_s=host_s)
            print(f'{rate} bit/s; host={host_s * 1000:.0f} ms/paquete; '
                  f'N={n}; aire={air:.4f} s; intercambios={exchange:.4f} s; '
                  f'trafico_RF_equiv={traffic:.0f} B; sobrecarga_RF={overhead:.4%}')
    n, _, _, _, _ = escenario_capacidad()
    print(f'Carga radio fija={n * 32} B; razon sobre carga radio={76800 / (n * 32):.4f}')
    print('No incluye fallos, reintentos, bloques de control, codificacion, guardado ni pantalla.')


if __name__ == '__main__':
    main()
