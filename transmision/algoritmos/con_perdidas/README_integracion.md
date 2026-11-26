# Guía de Integración en Raspberry Pi Zero (Receptor nRF24L01)

Esta guía resume cómo integrar los módulos de **decodificación (`decodificador.py`)** y **evaluación (`metricas.py`)** en la **Raspberry Pi Zero** receptora con el enlace **nRF24L01 (`pyRF24`)**.

---

## 1. Dependencias mínimas en la Raspberry Pi Zero

Los módulos `decodificador.py` y `metricas.py` están implementados exclusivamente con la **biblioteca estándar de Python** y **NumPy** (no requieren `Pillow` ni `matplotlib` en la Raspberry Pi):

```bash
sudo apt update && sudo apt install -y python3-numpy
# O dentro del entorno virtual del receptor:
python3 -m pip install numpy
```

---

## 2. Archivos que deben copiarse a cada nodo

- **Raspberry Pi Emisora (TX):**
  - `codificador.py` (requiere `numpy` y `Pillow`, o bien transmitir directamente los `.bin` pregenerados en `resultados/comprimidas/`).
  - Carpeta `imagenes/` con las 3 imágenes `.pgm` de prueba (`01_fotografica.pgm`, `02_areas_uniformes.pgm`, `03_detalle_fino.pgm`).
  - *Nota:* El codificador y `pruebas.py` aceptan imágenes de entrada en formato `.pgm` o `.bmp` (se convierten automáticamente a escala de grises de 8 bits si fuera necesario), mientras que el decodificador sigue generando archivos `.pgm` (P5).
- **Raspberry Pi Receptora (RX):**
  - `decodificador.py`
  - `metricas.py`
  - (Opcional, para calcular MSE/PSNR y BER in situ en el receptor): carpeta `imagenes/` y copia de referencia de `resultados/comprimidas/*.bin`.

---

## 3. Ejemplo de integración en el receptor (`pyRF24`)

Una vez que el script receptor de `pyRF24` termina de reensamblar los paquetes de una imagen en un objeto `bytes` (`datos_recibidos`), integren `descomprimir_pgm()` y `registrar_metricas_csv()` de la siguiente manera:

```python
from pathlib import Path
from decodificador import descomprimir_pgm
from metricas import (
    UMBRAL_PSNR_DB,
    calcular_ber,
    calcular_mse,
    calcular_psnr,
    calcular_razon_compresion,
    calcular_sobrecarga_protocolo,
    calcular_tasa_util,
    registrar_metricas_csv,
)


def leer_pgm_nativo(ruta_pgm: str | Path):
    """Lector PGM P5 sin Pillow para usar directamente en la Raspberry Pi RX."""
    import numpy as np
    datos = Path(ruta_pgm).read_bytes()
    lineas = []
    pos = 0
    while len(lineas) < 3:
        fin = datos.index(b'\n', pos)
        linea = datos[pos:fin].decode('ascii').strip()
        if not linea.startswith('#'):
            lineas.append(linea)
        pos = fin + 1
    ancho, alto = map(int, lineas[1].split())
    return np.frombuffer(datos[pos:pos + ancho * alto], dtype=np.uint8).reshape((alto, ancho))


def procesar_recepcion_rf(
    nombre_imagen: str,          # ej. '01_fotografica'
    datos_recibidos: bytes,      # flujo QPG1 reensamblado en RX
    bytes_transmitidos: int,     # total de bytes enviados por aire (incluyendo cabeceras de paquete RF)
    t_compresion_ms: float,      # tiempo medido en TX (o 0.0 si se envió el .bin precomprimido)
    t_transmision_ms: float,     # tiempo total de transmisión por el enlace nRF24L01 en ms
    ruta_pgm_original: Path,     # ej. Path('imagenes/01_fotografica.pgm')
    datos_enviados_ref: bytes,   # flujo .bin original enviado por TX (para medir BER)
    modo: str = 'rf_30m',
) -> None:
    # 1. Descomprimir en modo tolerante (estricto=False) para soportar relleno/longitud de tramas RF
    ruta_salida = Path('resultados_rf/reconstruidas') / f'{nombre_imagen}_rx.pgm'
    reconstruida, info = descomprimir_pgm(
        datos_recibidos,
        ruta_salida=ruta_salida,
        estricto=False,
    )

    bits = info['bits']
    ruta_final = ruta_salida.with_name(f'{nombre_imagen}_{bits}bits.pgm')
    ruta_salida.rename(ruta_final)

    # 2. Guardar también el binario crudo recibido para auditoría
    ruta_bin_rx = Path('resultados_rf/recibidos_bin') / f'{nombre_imagen}_{bits}bits_rx.bin'
    ruta_bin_rx.parent.mkdir(parents=True, exist_ok=True)
    ruta_bin_rx.write_bytes(datos_recibidos)

    # 3. Calcular métricas de calidad y enlace
    original = leer_pgm_nativo(ruta_pgm_original)
    bytes_original = ruta_pgm_original.stat().st_size
    bytes_comprimidos = len(datos_enviados_ref)
    t_descompresion_ms = info['tiempo_descompresion_s'] * 1000.0
    t_total_ms = t_compresion_ms + t_transmision_ms + t_descompresion_ms

    rc = calcular_razon_compresion(bytes_original, bytes_transmitidos)
    sobrecarga = calcular_sobrecarga_protocolo(bytes_comprimidos, bytes_transmitidos)
    tasa_util = calcular_tasa_util(bytes_comprimidos, t_transmision_ms / 1000.0)
    ber = calcular_ber(datos_enviados_ref, datos_recibidos)
    mse = calcular_mse(original, reconstruida)
    psnr_db = calcular_psnr(original, reconstruida)

    # 4. Registrar fila en el CSV oficial
    registrar_metricas_csv(
        'resultados_rf/metricas_enlace_30m.csv',
        {
            'imagen': nombre_imagen,
            'modo': modo,
            'bits': bits,
            'bytes_original': bytes_original,
            'bytes_comprimidos': bytes_comprimidos,
            'bytes_transmitidos': bytes_transmitidos,
            'razon_compresion': round(rc, 4),
            'sobrecarga_protocolo': round(sobrecarga, 6),
            't_compresion_ms': round(t_compresion_ms, 4),
            't_transmision_ms': round(t_transmision_ms, 4),
            't_descompresion_ms': round(t_descompresion_ms, 4),
            't_total_ms': round(t_total_ms, 4),
            'tasa_util_bps': round(tasa_util, 2),
            'ber': round(ber, 8),
            'mse': round(mse, 4),
            'psnr_db': round(psnr_db, 4),
            'cumple_25db': psnr_db >= UMBRAL_PSNR_DB,
        },
    )
```

---

## 4. Uso por línea de comandos (CLI) en la Raspberry Pi

Si el receptor guarda directamente cada archivo recibido como `.bin`, también pueden decodificarlo desde la terminal:

```bash
# Modo estricto (verifica longitud exacta y bits de relleno en cero):
python3 decodificador.py recibido.bin salida.pgm

# Modo tolerante para pruebas de RF (tolera bytes extra de tramas de 32 B o errores en relleno):
python3 decodificador.py recibido.bin salida.pgm --tolerante
```

---

## 5. Lista exacta de archivos y datos a devolver tras las pruebas a 30 m

Al finalizar las pruebas de campo a **30 metros** con los transceptores nRF24L01, por favor envíenme una carpeta comprimida (`.zip`) con:

1. **`metricas_enlace_30m.csv`**: archivo CSV generado con `registrar_metricas_csv()` para las **12 pruebas** (las 3 imágenes `01_fotografica`, `02_areas_uniformes`, `03_detalle_fino` evaluadas en `6, 4, 3 y 2` bits).
   - Con este CSV podré generar inmediatamente las gráficas finales ejecutando:
     ```bash
     python3 pruebas.py --csv resultados_rf/metricas_enlace_30m.csv --salida resultados_rf
     ```
2. **Carpeta `reconstruidas/`**: las 12 imágenes `.pgm` reconstruidas en la Raspberry Pi receptora (`<imagen>_<bits>bits.pgm`).
3. **Carpeta `recibidos_bin/`**: los 12 archivos binarios crudos `.bin` tal como fueron reensamblados en el receptor (`<imagen>_<bits>bits_rx.bin`), por si necesitamos recalcular BER o inspeccionar tramas dañadas.
4. **Parámetros del enlace nRF24L01 utilizados**:
   - Tasa de datos RF configurada (`250 kbps`, `1 Mbps` o `2 Mbps`), nivel de potencia PA, canal RF, tamaño de payload por paquete (ej. 32 B), número de reintentos automáticos (`ARD`/`ARC`) y cantidad de paquetes retransmitidos o perdidos observados.
