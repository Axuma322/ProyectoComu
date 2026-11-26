import argparse
import struct
from pathlib import Path
from time import perf_counter
import numpy as np
from PIL import Image

# Cabecera: magia (4 bytes), ancho (2), alto (2), bits (1).
CABECERA = struct.Struct('>4sHHB')


def leer_pgm(ruta):
    with Image.open(ruta) as img:
        if img.format not in ('PPM', 'BMP'):
            raise ValueError('Se requiere una imagen PGM o BMP sin compresión')
        if img.mode != 'L':
            img = img.convert('L')
        if not (1 <= img.width <= 320 and 1 <= img.height <= 240):
            raise ValueError('Dimensiones fuera del límite')
        return np.array(img, dtype=np.uint8)


def cuantizar(pixeles, bits):
    if not 1 <= bits <= 7:
        raise ValueError('bits debe estar entre 1 y 7')
    return pixeles >> (8 - bits)


def empaquetar_bits(cuantizados, bits):
    # Cada símbolo se convierte en bits, del más significativo al menos significativo.
    posiciones = np.arange(bits - 1, -1, -1, dtype=np.uint8)
    flujo = ((cuantizados.ravel()[:, None] >> posiciones) & 1).ravel()
    return np.packbits(flujo, bitorder='big').tobytes()


def comprimir_pgm(ruta, bits):
    pixeles = leer_pgm(ruta)
    alto, ancho = pixeles.shape
    cuantizados = cuantizar(pixeles, bits)
    carga = empaquetar_bits(cuantizados, bits)
    return CABECERA.pack(b'QPG1', ancho, alto, bits) + carga


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('imagen', type=Path)
    parser.add_argument('bits', type=int, choices=range(1, 8))
    parser.add_argument('salida', type=Path)
    args = parser.parse_args()
    inicio = perf_counter()
    datos = comprimir_pgm(args.imagen, args.bits)
    tiempo = perf_counter() - inicio
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    args.salida.write_bytes(datos)
    original = args.imagen.stat().st_size
    print(f'Original: {original} B | Comprimido: {len(datos)} B | RC local: {original/len(datos):.3f}:1 | Tiempo: {tiempo*1000:.3f} ms')


if __name__ == '__main__':
    main()