"""Adaptadores de los algoritmos del equipo. No acceden a radio, GPIO o red."""
from collections import Counter
import hashlib
import io
import math
from pathlib import Path
import struct
import time

from PIL import Image
from .algoritmos.algoritmo_sin_perdidas.compresor_sin_perdidas import huffmanCodes
from .algoritmos.algoritmo_sin_perdidas.descompresor_sin_perdidas import (
    read_huffman_header, build_tree, decompress_payload)

MAX_BYTES = 2 * 1024 * 1024
# HUF2: firma, longitud original de 32 bits y cantidad de símbolos de 16 bits.
HUFF = struct.Struct('>4sIH')


def validate_options(mode, bits=4):
    if mode not in {'sin_perdidas', 'con_perdidas', 'automatico'}:
        raise ValueError('Modo de codificación desconocido')
    if type(bits) is not int or not 1 <= bits <= 7:
        raise ValueError('La calidad debe ser un entero de 1 a 7 bits por píxel')
    return {'modo': mode, 'bits': bits}


def huffman_encode(data):
    """Codifica todos los bytes, no solo píxeles; conserva cabecera y paleta."""
    if not 1 <= len(data) <= MAX_BYTES:
        raise ValueError('Tamaño de archivo fuera del límite')
    codes = huffmanCodes({bytes([k]): v for k, v in Counter(data).items()})
    output = bytearray(HUFF.pack(b'HUF2', len(data), len(codes)))
    integer_codes = {}
    for symbol, code in sorted(codes.items()):
        n = len(code)
        output.extend(symbol + bytes([n]))
        output.extend((int(code, 2) << (-n % 8)).to_bytes((n + 7) // 8, 'big'))
        integer_codes[symbol[0]] = (int(code, 2), n)
    accumulator = count = 0
    for symbol in data:
        code, length = integer_codes[symbol]
        accumulator = (accumulator << length) | code
        count += length
        while count >= 8:
            count -= 8
            output.append((accumulator >> count) & 255)
        accumulator &= (1 << count) - 1
    if count:
        output.append(accumulator << (8 - count))
    return bytes(output)


def huffman_decode(data):
    """Lee la tabla transmitida y exige longitud y relleno exactos de HUF2."""
    if len(data) < HUFF.size:
        raise ValueError('Cabecera Huffman incompleta')
    magic, size, count = HUFF.unpack_from(data)
    if magic != b'HUF2' or not 1 <= size <= MAX_BYTES:
        raise ValueError('Cabecera Huffman inválida')
    stream = io.BytesIO(data[HUFF.size:])
    tree = build_tree(read_huffman_header(stream, count))
    return decompress_payload(stream.read(), tree, size)


def pixels(data):
    """Obtiene grises para medir calidad; no modifica el archivo fuente."""
    with Image.open(io.BytesIO(data)) as image:
        if not (1 <= image.width <= 320 and 1 <= image.height <= 240):
            raise ValueError('Dimensiones fuera del límite')
        image.load()
        return image.convert('L')


def decode(data, mode):
    """Reconstruye bytes del original o un PGM; QPG1 se lee en modo estricto."""
    if mode == 'sin_perdidas':
        return huffman_decode(data)
    if mode != 'con_perdidas':
        raise ValueError('Códec recibido desconocido')
    from .algoritmos.con_perdidas.decodificador import descomprimir_pgm
    matrix, info = descomprimir_pgm(data, estricto=True)
    return f'P5\n{info["ancho"]} {info["alto"]}\n255\n'.encode() + matrix.tobytes()


def encode(path, mode, bits=4):
    """Prepara un envío sin radio: codifica, reconstruye, mide y calcula hashes.

    Los candidatos automáticos se evalúan en TX. La validación local asegura el
    hash que luego exigirá RX, sin transportar una segunda copia del original.
    """
    validate_options(mode, bits)
    path = Path(path)
    original = path.read_bytes()
    if not 1 <= len(original) <= MAX_BYTES:
        raise ValueError('Tamaño de archivo fuera del límite')
    before = pixels(original)
    with Image.open(io.BytesIO(original)) as source:
        if source.format not in {'BMP', 'PPM'} or source.mode not in {'L', 'P', '1'}:
            raise ValueError('Se requiere BMP o PGM en escala de grises')
        if source.mode == 'P' and any(r != g or g != b for r, g, b in source.convert('RGB').getdata()):
            raise ValueError('La paleta de origen debe ser de grises')
    started = time.monotonic()
    if mode == 'automatico':
        # 25 dB es el objetivo de selección implementado, no una medición RF.
        candidates = [encode(path, 'sin_perdidas')]
        for level in range(1, 8):
            candidate = encode(path, 'con_perdidas', level)
            if candidate[1]['psnr_tx_db'] is None or candidate[1]['psnr_tx_db'] >= 25:
                candidates.append(candidate)
        result = min(candidates, key=lambda c: len(c[0]))
        result[1]['seleccion_automatica_ms'] = (time.monotonic() - started) * 1000
        return result
    if mode == 'sin_perdidas':
        encoded = huffman_encode(original)
        bits = None
    else:
        from .algoritmos.con_perdidas.codificador import comprimir_pgm
        encoded = comprimir_pgm(path, bits)
    compression_ms = (time.monotonic() - started) * 1000
    restored = decode(encoded, mode)
    # La comparación es local. RX recibe estos valores como calculados en TX;
    # comprueba el hash de su propia reconstrucción, no inventa calidad o BER.
    after = pixels(restored)
    if before.size != after.size:
        raise ValueError('El códec modificó las dimensiones')
    if mode == 'con_perdidas':
        import numpy as np
        from .algoritmos.con_perdidas.metricas import calcular_mse
        mse = calcular_mse(np.asarray(before), np.asarray(after))
    else:
        mse = 0.0
    if mode == 'sin_perdidas' and restored != original:
        raise ValueError('Huffman no recuperó el archivo original')
    return encoded, dict(modo=mode, bits=bits, nombre=path.name[-120:],
                        ancho=before.width, alto=before.height,
                        bytes_original=len(original), bytes_comprimidos=len(encoded),
                        sha256_original=hashlib.sha256(original).hexdigest(),
                        sha256_reconstruida=hashlib.sha256(restored).hexdigest(),
                        compresion_ms=compression_ms,
                        preparacion_tx_ms=(time.monotonic() - started) * 1000,
                        razon_compresion=len(original) / len(encoded), mse_tx=mse,
                        psnr_tx_db=None if mse == 0 else 10 * math.log10(255 ** 2 / mse))
