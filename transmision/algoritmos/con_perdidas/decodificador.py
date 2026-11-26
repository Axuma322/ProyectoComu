"""Decodificador de imágenes PGM cuantizadas uniformemente (formato QPG1).

Diseñado para ejecutarse en Raspberry Pi Zero sin dependencias externas
más allá de la biblioteca estándar de Python y NumPy.
"""

from __future__ import annotations

import argparse
import struct
from pathlib import Path
from time import perf_counter
import numpy as np

# Cabecera binaria de 9 bytes: magia (4B), ancho (uint16 BE), alto (uint16 BE), bits (uint8)
CABECERA = struct.Struct('>4sHHB')
MAGIA = b'QPG1'
ANCHO_MAX = 320
ALTO_MAX = 240


def leer_cabecera(datos_comprimidos: bytes) -> tuple[int, int, int]:
    """Valida y extrae (ancho, alto, bits) de la cabecera QPG1 de 9 bytes."""
    if not isinstance(datos_comprimidos, (bytes, bytearray, memoryview)):
        raise TypeError('datos_comprimidos debe ser bytes, bytearray o memoryview')
    if len(datos_comprimidos) < CABECERA.size:
        raise ValueError(
            f'Datos insuficientes para la cabecera: se requieren {CABECERA.size} bytes, '
            f'se recibieron {len(datos_comprimidos)}'
        )

    magia, ancho, alto, bits = CABECERA.unpack_from(datos_comprimidos)
    if magia != MAGIA:
        raise ValueError(f'Magia inválida en cabecera: se esperaba {MAGIA!r}, se recibió {magia!r}')
    if not (1 <= ancho <= ANCHO_MAX and 1 <= alto <= ALTO_MAX):
        raise ValueError(
            f'Dimensiones fuera de rango ({ancho}x{alto}); '
            f'deben estar entre 1x1 y {ANCHO_MAX}x{ALTO_MAX}'
        )
    if not (1 <= bits <= 7):
        raise ValueError(f'Profundidad de bits inválida ({bits}); debe estar entre 1 y 7')

    return int(ancho), int(alto), int(bits)


def desempaquetar_bits(
    datos_comprimidos: bytes,
    estricto: bool = True,
) -> tuple[np.ndarray, int, int, int]:
    """Desempaqueta el flujo continuo de símbolos cuantizados MSB-first.

    En modo estricto=True verifica que la longitud de la carga útil coincida
    exactamente con ceil(ancho * alto * bits / 8) y que los bits de relleno
    finales sean cero. En modo estricto=False tolera errores en bits de relleno
    o discrepancias de longitud propias de enlaces RF reales.
    """
    ancho, alto, bits = leer_cabecera(datos_comprimidos)
    n_pixeles = ancho * alto
    n_bits_utiles = n_pixeles * bits
    bytes_esperados = (n_bits_utiles + 7) // 8

    carga = memoryview(datos_comprimidos)[CABECERA.size:]

    if estricto and len(carga) != bytes_esperados:
        raise ValueError(
            f'Longitud de carga útil inválida: se esperaban {bytes_esperados} bytes '
            f'para {ancho}x{alto} a {bits} bits, se recibieron {len(carga)}'
        )

    bytes_carga = np.frombuffer(carga, dtype=np.uint8)
    flujo_bits = np.unpackbits(bytes_carga, bitorder='big')

    if estricto:
        bits_relleno = flujo_bits[n_bits_utiles:]
        if bits_relleno.any():
            raise ValueError('Los bits de relleno al final del flujo no son todos cero')
    else:
        if flujo_bits.size < n_bits_utiles:
            flujo_bits = np.pad(
                flujo_bits,
                (0, n_bits_utiles - flujo_bits.size),
                mode='constant',
                constant_values=0,
            )

    bits_simbolos = flujo_bits[:n_bits_utiles].reshape(n_pixeles, bits)
    pesos = (1 << np.arange(bits - 1, -1, -1, dtype=np.uint16))
    cuantizados = (bits_simbolos @ pesos).astype(np.uint8)

    return cuantizados, ancho, alto, bits


def reconstruir_pixeles(
    cuantizados: np.ndarray,
    ancho: int,
    alto: int,
    bits: int,
) -> np.ndarray:
    """Reconstruye las intensidades de 8 bits usando el punto medio del intervalo."""
    if not (1 <= ancho <= ANCHO_MAX and 1 <= alto <= ALTO_MAX):
        raise ValueError(
            f'Dimensiones fuera de rango ({ancho}x{alto}); '
            f'deben estar entre 1x1 y {ANCHO_MAX}x{ALTO_MAX}'
        )
    if not (1 <= bits <= 7):
        raise ValueError(f'Profundidad de bits inválida ({bits}); debe estar entre 1 y 7')

    arr = np.asarray(cuantizados)
    if arr.size != ancho * alto:
        raise ValueError(
            f'La cantidad de símbolos cuantizados ({arr.size}) no coincide con '
            f'ancho * alto ({ancho * alto})'
        )

    q16 = arr.astype(np.uint16, copy=False)
    desplazamiento = 8 - bits
    punto_medio = 1 << (7 - bits)
    reconstruidos = (q16 << desplazamiento) + punto_medio

    return reconstruidos.astype(np.uint8).reshape((alto, ancho))


def guardar_pgm(matriz: np.ndarray, ruta_salida: str | Path) -> None:
    """Guarda una matriz 2D uint8 como archivo PGM binario (P5) con máximo 255."""
    arr = np.asarray(matriz)
    if arr.ndim != 2:
        raise ValueError(f'Se requiere una matriz 2D para guardar PGM, se recibió ndim={arr.ndim}')
    alto, ancho = arr.shape
    if not (1 <= ancho <= ANCHO_MAX and 1 <= alto <= ALTO_MAX):
        raise ValueError(
            f'Dimensiones fuera de rango ({ancho}x{alto}); '
            f'deben estar entre 1x1 y {ANCHO_MAX}x{ALTO_MAX}'
        )

    arr_u8 = np.ascontiguousarray(arr, dtype=np.uint8)
    cabecera_pgm = f'P5\n{ancho} {alto}\n255\n'.encode('ascii')

    ruta = Path(ruta_salida)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_bytes(cabecera_pgm + arr_u8.tobytes())


def descomprimir_pgm(
    datos_comprimidos: bytes,
    ruta_salida: str | Path | None = None,
    estricto: bool = True,
) -> tuple[np.ndarray, dict]:
    """Descomprime un flujo QPG1 a matriz 2D uint8, guardando opcionalmente en PGM P5."""
    inicio = perf_counter()
    cuantizados, ancho, alto, bits = desempaquetar_bits(datos_comprimidos, estricto=estricto)
    matriz = reconstruir_pixeles(cuantizados, ancho, alto, bits)
    tiempo_descompresion_s = perf_counter() - inicio

    if ruta_salida is not None:
        guardar_pgm(matriz, ruta_salida)

    info = {
        'ancho': ancho,
        'alto': alto,
        'bits': bits,
        'bytes_comprimidos': len(datos_comprimidos),
        'tiempo_descompresion_s': tiempo_descompresion_s,
    }
    return matriz, info


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Decodifica un archivo binario QPG1 a imagen PGM (P5).'
    )
    parser.add_argument('entrada', type=Path, help='Ruta del archivo comprimido (.bin)')
    parser.add_argument('salida', type=Path, help='Ruta de la imagen PGM reconstruida (.pgm)')
    parser.add_argument(
        '--tolerante',
        action='store_true',
        help='Tolera errores en bits de relleno o longitud extra en pruebas de enlace RF',
    )
    args = parser.parse_args()

    datos = args.entrada.read_bytes()
    _, info = descomprimir_pgm(datos, ruta_salida=args.salida, estricto=not args.tolerante)
    bytes_pgm = args.salida.stat().st_size
    tiempo_ms = info['tiempo_descompresion_s'] * 1000.0
    print(
        f"Comprimido: {info['bytes_comprimidos']} B | "
        f"PGM: {bytes_pgm} B ({info['ancho']}x{info['alto']}, {info['bits']} bits) | "
        f"Tiempo: {tiempo_ms:.3f} ms"
    )


if __name__ == '__main__':
    main()
