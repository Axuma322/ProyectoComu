"""Suite de pruebas locales, evaluación cuantitativa y generación de gráficos.

Evalúa el desempeño de compresión y reconstrucción QPG1 sobre las imágenes de
prueba o grafica directamente un archivo CSV obtenido en el enlace inalámbrico.
"""

from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path
from time import perf_counter
from typing import Sequence

# Evitar advertencias de permisos en entornos donde ~/.config/matplotlib no es escribible
os.environ.setdefault('MPLCONFIGDIR', '/tmp/matplotlib_ie0527')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from codificador import CABECERA, comprimir_pgm, empaquetar_bits, leer_pgm
from decodificador import (
    descomprimir_pgm,
    desempaquetar_bits,
    guardar_pgm,
    leer_cabecera,
    reconstruir_pixeles,
)
from metricas import (
    UMBRAL_PSNR_DB,
    calcular_ber,
    calcular_mse,
    calcular_psnr,
    calcular_razon_compresion,
    calcular_sobrecarga_protocolo,
    calcular_tasa_util,
    registrar_metricas_csv,
    verificar_identidad_bit_a_bit,
)

BASE = Path(__file__).resolve().parent
BITS_POR_DEFECTO = (6, 4, 3, 2)


def verificar_contrato() -> None:
    """Verifica el contrato binario QPG1 con los vectores de referencia."""
    # Vector 1: [9, 6] a 4 bits -> b'\x96'
    v1_q = np.array([9, 6], dtype=np.uint8)
    v1_carga = empaquetar_bits(v1_q, 4)
    assert v1_carga == b'\x96', f'Empaquetado 4 bits inesperado: {v1_carga!r}'
    v1_bin = CABECERA.pack(b'QPG1', 2, 1, 4) + v1_carga
    assert leer_cabecera(v1_bin) == (2, 1, 4)
    q_dec1, w1, h1, b1 = desempaquetar_bits(v1_bin, estricto=True)
    assert (w1, h1, b1) == (2, 1, 4)
    assert np.array_equal(q_dec1, v1_q), f'Desempaquetado 4 bits falló: {q_dec1} != {v1_q}'
    rec1 = reconstruir_pixeles(q_dec1, w1, h1, b1)
    assert np.array_equal(rec1, np.array([[152, 104]], dtype=np.uint8))

    # Vector 2: [5, 2, 7] a 3 bits -> b'\xab\x80'
    v2_q = np.array([5, 2, 7], dtype=np.uint8)
    v2_carga = empaquetar_bits(v2_q, 3)
    assert v2_carga == b'\xab\x80', f'Empaquetado 3 bits inesperado: {v2_carga!r}'
    v2_bin = CABECERA.pack(b'QPG1', 3, 1, 3) + v2_carga
    assert leer_cabecera(v2_bin) == (3, 1, 3)
    q_dec2, w2, h2, b2 = desempaquetar_bits(v2_bin, estricto=True)
    assert (w2, h2, b2) == (3, 1, 3)
    assert np.array_equal(q_dec2, v2_q), f'Desempaquetado 3 bits falló: {q_dec2} != {v2_q}'
    rec2 = reconstruir_pixeles(q_dec2, w2, h2, b2)
    assert np.array_equal(rec2, np.array([[176, 80, 240]], dtype=np.uint8))

    # Verificación de modo estricto vs. modo tolerante con bits de relleno alterados / bytes extra
    v2_relleno_sucio = CABECERA.pack(b'QPG1', 3, 1, 3) + b'\xab\xbf\x00'
    try:
        desempaquetar_bits(v2_relleno_sucio, estricto=True)
        raise AssertionError('Modo estricto debía rechazar longitud extra y relleno no nulo')
    except ValueError:
        pass

    q_tol, _, _, _ = desempaquetar_bits(v2_relleno_sucio, estricto=False)
    assert np.array_equal(q_tol, v2_q), 'Modo tolerante no recuperó los símbolos esperados'


def _cargar_filas_csv(ruta_csv: str | Path) -> list[dict]:
    """Lee un archivo CSV de métricas y convierte los campos numéricos."""
    ruta = Path(ruta_csv)
    filas: list[dict] = []
    with ruta.open('r', newline='', encoding='utf-8') as archivo:
        lector = csv.DictReader(archivo)
        for f in lector:
            cumple_raw = str(f.get('cumple_25db', '')).strip().lower()
            cumple_bool = cumple_raw in ('true', '1', 'si', 'sí', 'yes')
            filas.append({
                'imagen': str(f['imagen']),
                'modo': str(f.get('modo', 'local')),
                'bits': int(f['bits']),
                'bytes_original': int(float(f['bytes_original'])),
                'bytes_comprimidos': int(float(f['bytes_comprimidos'])),
                'bytes_transmitidos': int(float(f['bytes_transmitidos'])),
                'razon_compresion': float(f['razon_compresion']),
                'sobrecarga_protocolo': float(f.get('sobrecarga_protocolo', 0.0) or 0.0),
                't_compresion_ms': float(f.get('t_compresion_ms', 0.0) or 0.0),
                't_transmision_ms': float(f.get('t_transmision_ms', 0.0) or 0.0),
                't_descompresion_ms': float(f.get('t_descompresion_ms', 0.0) or 0.0),
                't_total_ms': float(f.get('t_total_ms', 0.0) or 0.0),
                'tasa_util_bps': float(f.get('tasa_util_bps', 0.0) or 0.0),
                'ber': float(f.get('ber', 0.0) or 0.0),
                'mse': float(f['mse']),
                'psnr_db': float(f['psnr_db']),
                'cumple_25db': cumple_bool,
            })
    return filas


def imprimir_tabla_resultados(filas: Sequence[dict]) -> None:
    """Imprime en consola una tabla formateada con los resultados del estudio."""
    encabezado = (
        f"{'Imagen':<22} {'Bits':>4} {'Orig(B)':>8} {'Comp(B)':>8} "
        f"{'RC':>7} {'MSE':>8} {'PSNR(dB)':>9} {'>=25dB':>7} "
        f"{'T_comp(ms)':>10} {'T_desc(ms)':>10} {'T_tot(ms)':>10}"
    )
    separador = '-' * len(encabezado)
    print(separador)
    print(encabezado)
    print(separador)
    for fila in filas:
        cumple_txt = 'SI' if fila['cumple_25db'] else 'NO'
        print(
            f"{fila['imagen']:<22} {int(fila['bits']):>4d} "
            f"{int(fila['bytes_original']):>8d} {int(fila['bytes_comprimidos']):>8d} "
            f"{float(fila['razon_compresion']):>6.3f}x "
            f"{float(fila['mse']):>8.2f} {float(fila['psnr_db']):>9.2f} "
            f"{cumple_txt:>7} "
            f"{float(fila['t_compresion_ms']):>10.3f} "
            f"{float(fila['t_descompresion_ms']):>10.3f} "
            f"{float(fila['t_total_ms']):>10.3f}"
        )
    print(separador)


def probar_configuraciones(
    directorio_imagenes: str | Path = BASE / 'imagenes',
    lista_bits: Sequence[int] = BITS_POR_DEFECTO,
    directorio_resultados: str | Path = BASE / 'resultados',
    modo: str = 'local',
) -> list[dict]:
    """Ejecuta la cadena de codificación, decodificación y evaluación de métricas."""
    verificar_contrato()

    dir_img = Path(directorio_imagenes)
    dir_res = Path(directorio_resultados)
    dir_comp = dir_res / 'comprimidas'
    dir_rec = dir_res / 'reconstruidas'
    ruta_csv = dir_res / 'metricas_cuantizacion.csv'

    dir_comp.mkdir(parents=True, exist_ok=True)
    dir_rec.mkdir(parents=True, exist_ok=True)
    if ruta_csv.exists():
        ruta_csv.unlink()

    rutas_pgm = sorted(
        p for p in dir_img.iterdir()
        if p.is_file() and p.suffix.lower() in ('.pgm', '.bmp')
    )
    if not rutas_pgm:
        raise FileNotFoundError(f'No se encontraron imágenes .pgm o .bmp en {dir_img}')

    filas: list[dict] = []

    for ruta_img in rutas_pgm:
        original = leer_pgm(ruta_img)
        bytes_original = ruta_img.stat().st_size

        for bits in lista_bits:
            t_inicio_comp = perf_counter()
            datos_comprimidos = comprimir_pgm(ruta_img, bits)
            t_compresion_ms = (perf_counter() - t_inicio_comp) * 1000.0

            nombre_base = f'{ruta_img.stem}_{bits}bits'
            ruta_bin = dir_comp / f'{nombre_base}.bin'
            ruta_bin.write_bytes(datos_comprimidos)

            ruta_pgm_rec = dir_rec / f'{nombre_base}.pgm'
            reconstruida, info = descomprimir_pgm(
                datos_comprimidos,
                ruta_salida=ruta_pgm_rec,
                estricto=True,
            )

            # Verificar que el archivo PGM guardado es compatible con leer_pgm y exacto
            reconstruida_disco = leer_pgm(ruta_pgm_rec)
            assert verificar_identidad_bit_a_bit(reconstruida, reconstruida_disco), (
                f'Discrepancia entre matriz en memoria y PGM guardado en {ruta_pgm_rec}'
            )

            bytes_comprimidos = info['bytes_comprimidos']
            bytes_transmitidos = bytes_comprimidos
            t_transmision_ms = 0.0
            t_descompresion_ms = info['tiempo_descompresion_s'] * 1000.0
            t_total_ms = t_compresion_ms + t_transmision_ms + t_descompresion_ms

            razon_compresion = calcular_razon_compresion(bytes_original, bytes_transmitidos)
            sobrecarga = calcular_sobrecarga_protocolo(bytes_comprimidos, bytes_transmitidos)
            tasa_util_bps = calcular_tasa_util(bytes_comprimidos, t_transmision_ms / 1000.0)
            ber = calcular_ber(datos_comprimidos, datos_comprimidos)
            mse = calcular_mse(original, reconstruida)
            psnr_db = calcular_psnr(original, reconstruida)
            cumple_25db = psnr_db >= UMBRAL_PSNR_DB

            fila = {
                'imagen': ruta_img.stem,
                'modo': modo,
                'bits': int(bits),
                'bytes_original': int(bytes_original),
                'bytes_comprimidos': int(bytes_comprimidos),
                'bytes_transmitidos': int(bytes_transmitidos),
                'razon_compresion': round(razon_compresion, 4),
                'sobrecarga_protocolo': round(sobrecarga, 6),
                't_compresion_ms': round(t_compresion_ms, 4),
                't_transmision_ms': round(t_transmision_ms, 4),
                't_descompresion_ms': round(t_descompresion_ms, 4),
                't_total_ms': round(t_total_ms, 4),
                'tasa_util_bps': round(tasa_util_bps, 2),
                'ber': round(ber, 8),
                'mse': round(mse, 4),
                'psnr_db': round(psnr_db, 4),
                'cumple_25db': cumple_25db,
            }
            registrar_metricas_csv(ruta_csv, fila)
            filas.append(fila)

    return filas


def generar_graficos(
    fuente: str | Path | Sequence[dict] = BASE / 'resultados' / 'metricas_cuantizacion.csv',
    directorio_salida: str | Path = BASE / 'resultados',
) -> tuple[Path, Path]:
    """Genera los gráficos de curva tasa-distorsión y comparación tamaño vs. PSNR."""
    if isinstance(fuente, (str, Path)):
        filas = _cargar_filas_csv(fuente)
    else:
        filas = list(fuente)

    if not filas:
        raise ValueError('No hay datos de métricas para graficar')

    dir_out = Path(directorio_salida)
    dir_out.mkdir(parents=True, exist_ok=True)

    # 1. Gráfico: Curva Tasa-Distorsión (PSNR vs Razón de Compresión)
    ruta_curva = dir_out / 'curva_tasa_distorsion.png'
    fig, ax = plt.subplots(figsize=(8.5, 5.5))

    imagenes = sorted({f['imagen'] for f in filas})
    marcadores = ['o', 's', '^', 'D', 'v', 'P']

    for idx, nombre_img in enumerate(imagenes):
        sub = sorted(
            [f for f in filas if f['imagen'] == nombre_img],
            key=lambda x: x['razon_compresion'],
        )
        x_rc = [f['razon_compresion'] for f in sub]
        y_psnr = [f['psnr_db'] for f in sub]
        marcador = marcadores[idx % len(marcadores)]

        ax.plot(
            x_rc,
            y_psnr,
            marker=marcador,
            linewidth=2.0,
            markersize=7,
            label=nombre_img,
        )

        desplazamientos = [(6, 7), (6, -13), (-36, -11), (6, 14)]
        dx, dy = desplazamientos[idx % len(desplazamientos)]
        for f in sub:
            ax.annotate(
                f"{int(f['bits'])} bits",
                xy=(f['razon_compresion'], f['psnr_db']),
                xytext=(dx, dy),
                textcoords='offset points',
                fontsize=8.5,
            )

    ax.axhline(
        UMBRAL_PSNR_DB,
        color='#d62728',
        linestyle='--',
        linewidth=1.6,
        label=f'Umbral mínimo ({UMBRAL_PSNR_DB:.0f} dB)',
    )
    ax.set_title('Curva Tasa-Distorsión: PSNR vs. Razón de Compresión', fontsize=12, fontweight='bold')
    ax.set_xlabel('Razón de Compresión (RC = bytes_original / bytes_transmitidos)', fontsize=10.5)
    ax.set_ylabel('PSNR (dB)', fontsize=10.5)
    ax.grid(True, linestyle=':', alpha=0.7)
    ax.legend(loc='best', frameon=True)
    fig.tight_layout()
    fig.savefig(ruta_curva, dpi=200)
    plt.close(fig)

    # 2. Gráfico: Comparación Tamaño en KB vs. PSNR promedio por profundidad de bits
    ruta_comparacion = dir_out / 'comparacion_tamano_psnr.png'
    niveles_bits = sorted({int(f['bits']) for f in filas}, reverse=True)
    tamanos_kb = []
    psnr_promedios = []

    for b in niveles_bits:
        sub_b = [f for f in filas if int(f['bits']) == b]
        tam_medio_kb = float(np.mean([f['bytes_comprimidos'] / 1024.0 for f in sub_b]))
        psnr_medio = float(np.mean([f['psnr_db'] for f in sub_b]))
        tamanos_kb.append(tam_medio_kb)
        psnr_promedios.append(psnr_medio)

    etiquetas_x = [f'{b} bits' for b in niveles_bits]
    pos_x = np.arange(len(niveles_bits))

    fig, ax1 = plt.subplots(figsize=(8.5, 5.5))
    color_barras = '#1f77b4'
    color_linea = '#ff7f0e'

    barras = ax1.bar(
        pos_x - 0.12,
        tamanos_kb,
        width=0.45,
        color=color_barras,
        alpha=0.85,
        label='Tamaño comprimido (KB)',
    )
    ax1.set_xlabel('Profundidad de Cuantización', fontsize=10.5)
    ax1.set_ylabel('Tamaño del Archivo Comprimido (KB)', color=color_barras, fontsize=10.5)
    ax1.tick_params(axis='y', labelcolor=color_barras)
    ax1.set_xticks(pos_x)
    ax1.set_xticklabels(etiquetas_x)
    ax1.set_ylim(0, max(tamanos_kb) * 1.25 if tamanos_kb else 1.0)
    ax1.grid(True, axis='y', linestyle=':', alpha=0.6)

    for barra, val_kb in zip(barras, tamanos_kb):
        ax1.annotate(
            f'{val_kb:.1f} KB',
            xy=(barra.get_x() + barra.get_width() / 2.0, val_kb),
            xytext=(0, 4),
            textcoords='offset points',
            ha='center',
            va='bottom',
            fontsize=8.5,
            color=color_barras,
            fontweight='bold',
        )

    ax2 = ax1.twinx()
    linea_psnr = ax2.plot(
        pos_x + 0.12,
        psnr_promedios,
        color=color_linea,
        marker='o',
        linewidth=2.2,
        markersize=8,
        label='PSNR promedio (dB)',
    )
    umbral_line = ax2.axhline(
        UMBRAL_PSNR_DB,
        color='#d62728',
        linestyle='--',
        linewidth=1.5,
        label=f'Umbral {UMBRAL_PSNR_DB:.0f} dB',
    )
    ax2.set_ylabel('PSNR Promedio (dB)', color=color_linea, fontsize=10.5)
    ax2.tick_params(axis='y', labelcolor=color_linea)
    max_psnr = max(psnr_promedios + [UMBRAL_PSNR_DB]) if psnr_promedios else 40.0
    ax2.set_ylim(0, max_psnr * 1.2)

    for x_val, val_psnr in zip(pos_x + 0.12, psnr_promedios):
        ax2.annotate(
            f'{val_psnr:.1f} dB',
            xy=(x_val, val_psnr),
            xytext=(0, 8),
            textcoords='offset points',
            ha='center',
            va='bottom',
            fontsize=8.5,
            color='#b85600',
            fontweight='bold',
        )

    manejadores = [barras, linea_psnr[0], umbral_line]
    etiquetas_leyenda = [m.get_label() for m in manejadores]
    ax1.legend(manejadores, etiquetas_leyenda, loc='upper right', frameon=True)
    ax1.set_title(
        'Comparación de Tamaño Comprimido (KB) vs. PSNR Promedio por Profundidad de Bits',
        fontsize=11.5,
        fontweight='bold',
    )

    fig.tight_layout()
    fig.savefig(ruta_comparacion, dpi=200)
    plt.close(fig)

    return ruta_curva, ruta_comparacion


def _parsear_bits(valores_raw: Sequence[str]) -> list[int]:
    """Convierte argumentos de --bits (separados por espacios o comas) en lista de int."""
    resultado: list[int] = []
    for token in valores_raw:
        for parte in token.split(','):
            parte = parte.strip()
            if not parte:
                continue
            b = int(parte)
            if not (1 <= b <= 7):
                raise ValueError(f'Cada profundidad de bits debe estar entre 1 y 7 (recibido: {b})')
            resultado.append(b)
    if not resultado:
        raise ValueError('Se debe especificar al menos una profundidad de bits')
    return resultado


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Ejecuta las pruebas de cuantización y genera tablas CSV y gráficos PNG.'
    )
    parser.add_argument(
        '--bits',
        nargs='+',
        default=['6', '4', '3', '2'],
        help='Profundidades de bits a evaluar (por defecto: 6 4 3 2)',
    )
    parser.add_argument(
        '--csv',
        type=Path,
        default=None,
        help='Ruta de un CSV existente (p. ej. medido en enlace RF) para graficar sin recodificar',
    )
    parser.add_argument(
        '--imagenes',
        type=Path,
        default=BASE / 'imagenes',
        help='Directorio con imágenes .pgm de entrada',
    )
    parser.add_argument(
        '--salida',
        type=Path,
        default=BASE / 'resultados',
        help='Directorio de salida para resultados y gráficos',
    )
    args = parser.parse_args()

    if args.csv is not None:
        filas = _cargar_filas_csv(args.csv)
        imprimir_tabla_resultados(filas)
        ruta_curva, ruta_comp = generar_graficos(args.csv, directorio_salida=args.salida)
        print(f'Gráficos generados desde CSV ({args.csv}):')
        print(f'  - {ruta_curva}')
        print(f'  - {ruta_comp}')
        return

    lista_bits = _parsear_bits(args.bits)
    filas = probar_configuraciones(
        directorio_imagenes=args.imagenes,
        lista_bits=lista_bits,
        directorio_resultados=args.salida,
    )
    imprimir_tabla_resultados(filas)
    ruta_curva, ruta_comp = generar_graficos(filas, directorio_salida=args.salida)
    print(f"CSV guardado en: {args.salida / 'metricas_cuantizacion.csv'}")
    print(f'Gráficos generados (200 dpi):')
    print(f'  - {ruta_curva}')
    print(f'  - {ruta_comp}')


if __name__ == '__main__':
    main()
