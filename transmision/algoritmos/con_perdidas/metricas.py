"""Métricas de evaluación de calidad de imagen, compresión y desempeño de enlace.

Usa únicamente la biblioteca estándar de Python y NumPy para permitir su
importación directa en la Raspberry Pi Zero receptora.
"""

from __future__ import annotations

import csv
from pathlib import Path
import numpy as np

UMBRAL_PSNR_DB = 25.0

COLUMNAS_CSV = [
    'imagen',
    'modo',
    'bits',
    'bytes_original',
    'bytes_comprimidos',
    'bytes_transmitidos',
    'razon_compresion',
    'sobrecarga_protocolo',
    't_compresion_ms',
    't_transmision_ms',
    't_descompresion_ms',
    't_total_ms',
    'tasa_util_bps',
    'ber',
    'mse',
    'psnr_db',
    'cumple_25db',
]


def calcular_mse(original: np.ndarray, reconstruida: np.ndarray) -> float:
    """Calcula el Error Cuadrático Medio (MSE) operando en float64."""
    orig = np.asarray(original, dtype=np.float64)
    rec = np.asarray(reconstruida, dtype=np.float64)
    if orig.shape != rec.shape:
        raise ValueError(
            f'Las dimensiones de las imágenes no coinciden: {orig.shape} vs {rec.shape}'
        )
    if orig.size == 0:
        raise ValueError('Las matrices de imagen no pueden estar vacías')

    diferencia = orig - rec
    return float(np.mean(diferencia * diferencia))


def calcular_psnr(
    original: np.ndarray,
    reconstruida: np.ndarray,
    max_val: float = 255.0,
) -> float:
    """Calcula la Relación Señal a Ruido Pico (PSNR) en dB.

    Devuelve float('inf') si MSE == 0.
    """
    if max_val <= 0:
        raise ValueError('max_val debe ser mayor que cero')

    mse = calcular_mse(original, reconstruida)
    if mse == 0.0:
        return float('inf')

    return float(10.0 * np.log10((float(max_val) ** 2) / mse))


def calcular_razon_compresion(bytes_original: int, bytes_transmitidos: int) -> float:
    """Calcula la razón de compresión RC = bytes_original / bytes_transmitidos."""
    if bytes_original <= 0:
        raise ValueError('bytes_original debe ser mayor que cero')
    if bytes_transmitidos <= 0:
        raise ValueError('bytes_transmitidos debe ser mayor que cero')

    return float(bytes_original) / float(bytes_transmitidos)


def calcular_sobrecarga_protocolo(
    bytes_comprimidos: int,
    bytes_transmitidos: int | None = None,
    en_porcentaje: bool = False,
) -> float:
    """Calcula la sobrecarga relativa introducida por el protocolo de transporte.

    Definida como (bytes_transmitidos - bytes_comprimidos) / bytes_comprimidos.
    Si bytes_transmitidos es None, asume bytes_transmitidos == bytes_comprimidos (0.0).
    """
    if bytes_comprimidos <= 0:
        raise ValueError('bytes_comprimidos debe ser mayor que cero')
    if bytes_transmitidos is None:
        return 0.0
    if bytes_transmitidos < bytes_comprimidos:
        raise ValueError('bytes_transmitidos no puede ser menor que bytes_comprimidos')

    sobrecarga = float(bytes_transmitidos - bytes_comprimidos) / float(bytes_comprimidos)
    return sobrecarga * 100.0 if en_porcentaje else sobrecarga


def calcular_tasa_util(bytes_utiles: int, tiempo_transmision_s: float) -> float:
    """Calcula la tasa útil (goodput) en bits por segundo (bps)."""
    if bytes_utiles < 0:
        raise ValueError('bytes_utiles no puede ser negativo')
    if tiempo_transmision_s <= 0.0:
        return 0.0

    return float(bytes_utiles * 8) / float(tiempo_transmision_s)


def calcular_ber(datos_enviados: bytes, datos_recibidos: bytes) -> float:
    """Calcula la Tasa de Error de Bit (BER) vectorizada entre dos flujos de bytes."""
    env = np.frombuffer(memoryview(datos_enviados), dtype=np.uint8)
    rec = np.frombuffer(memoryview(datos_recibidos), dtype=np.uint8)

    if env.size == 0 and rec.size == 0:
        return 0.0
    if env.size == 0:
        return 1.0

    n_comun = min(env.size, rec.size)
    errores_comunes = 0
    if n_comun > 0:
        xor_bytes = np.bitwise_xor(env[:n_comun], rec[:n_comun])
        errores_comunes = int(np.unpackbits(xor_bytes, bitorder='big').sum())

    errores_longitud = abs(env.size - rec.size) * 8
    total_bits = max(env.size, rec.size) * 8
    return float(errores_comunes + errores_longitud) / float(total_bits)


def verificar_identidad_bit_a_bit(
    datos_a: bytes | bytearray | memoryview | np.ndarray,
    datos_b: bytes | bytearray | memoryview | np.ndarray,
) -> bool:
    """Verifica de forma vectorizada si dos flujos de bytes o matrices son idénticos."""
    es_bytes_a = isinstance(datos_a, (bytes, bytearray, memoryview))
    es_bytes_b = isinstance(datos_b, (bytes, bytearray, memoryview))

    if es_bytes_a and es_bytes_b:
        if len(datos_a) != len(datos_b):
            return False
        arr_a = np.frombuffer(memoryview(datos_a), dtype=np.uint8)
        arr_b = np.frombuffer(memoryview(datos_b), dtype=np.uint8)
        return bool(np.array_equal(arr_a, arr_b))

    arr_a = np.asarray(datos_a)
    arr_b = np.asarray(datos_b)
    if arr_a.shape != arr_b.shape:
        return False
    return bool(np.array_equal(arr_a, arr_b))


def registrar_metricas_csv(ruta_csv: str | Path, fila: dict) -> None:
    """Agrega una fila de métricas al archivo CSV oficial del estudio.

    Si el archivo no existe o está vacío, escribe primero la cabecera con
    COLUMNAS_CSV.
    """
    ruta = Path(ruta_csv)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    escribir_cabecera = not ruta.exists() or ruta.stat().st_size == 0

    fila_normalizada = {col: fila.get(col, '') for col in COLUMNAS_CSV}

    with ruta.open('a', newline='', encoding='utf-8') as archivo:
        escritor = csv.DictWriter(
            archivo,
            fieldnames=COLUMNAS_CSV,
            extrasaction='ignore',
        )
        if escribir_cabecera:
            escritor.writeheader()
        escritor.writerow(fila_normalizada)
