# Normativa y presupuesto de enlace

Conservamos la revisión de fuentes realizada el 16 de octubre de 2026. Todavía debemos confirmar la normativa consolidada y la identificación del módulo y su antena antes de fijar la configuración de prueba. Trabajar en ISM no basta para declarar un equipo conforme. [Fuentes L, L26 y S](fuentes.md)

## Bandas y potencia

El PNAF base es el decreto 44010-MICITT. La copia MICITT consultada es anterior a la reforma 45769-MICITT del 29 de abril de 2026. Su tabla 22, pp. 73–75 del PDF de La Gaceta, recoge:

| Banda candidata | Máxima salida / PIRE de la tabla | Punto por comprobar |
|---|---|---|
| nRF24: 2400–2500 MHz | 30 / 36 dBm | Módulo, antena, ancho ocupado y homologación |
| CC1101: 433,05–434,79 MHz | 24 / 30 dBm | Que el perfil RF quepa en la banda y cumpla emisiones |
| CC1101: 902–915 MHz | 24 / 30 dBm | Módulo y antena para esa banda |
| CC1101: 915–921 MHz | 30 / 36 dBm; menciona transmisión inalámbrica de potencia | Confirmar aplicabilidad a datos antes de usar esta fila |
| CC1101: 921–928 MHz | Dentro de 921–960: 24 / 30 dBm | Compatibilidad y condiciones del equipo |

Son límites de la referencia consultada, no potencias que proponemos utilizar. La excepción para enlaces **fijos** punto a punto en 2400–2500 MHz exige reducir salida 1 dB por cada 3 dBi de ganancia por encima de 6 dBi; no asumimos que nuestro montaje portátil califica. No trasladamos autorizaciones de 868 MHz ni límites FCC/CE a Costa Rica. [Reforma L26](https://www.imprentanacional.go.cr/pub/2026/04/29/ALCA45_29_04_2026.pdf)

Debemos revisar si hubo reformas posteriores y confirmar con el laboratorio la homologación aplicable al prototipo. SUTEL publica el procedimiento RCS-245-2023. También hay que comprobar potencia, ganancia, pérdidas de cable, ancho ocupado y espurias. Las condiciones generales exigen no causar interferencias, no reclamar protección y suspender emisión si se ocasiona interferencia. [L y S](fuentes.md)

## Cálculo hipotético

Usamos [UIT-R P.525-5, §2.3](https://www.itu.int/rec/R-REC-P.525-5-202411-I/en) para espacio libre:

```text
Lfs = 20 log10(4 pi d f / c)           d en m, f en Hz
Pr = Pt + Gt + Gr - Lfs - Ladicional   potencias en dBm, ganancias/pérdidas en dB
Margen = Pr - sensibilidad
PIRE = Pt + Gt - pérdida de cable TX
```

Supuestos: 2440 MHz, Pt=0 dBm, Gt=Gr=0 dBi y pérdidas adicionales conjuntas de 3 dB. No conocemos aún esos valores para las placas reales.

| Distancia | Lfs | Pr | Margen a 250 kbit/s | A 1 Mbit/s | A 2 Mbit/s |
|---|---:|---:|---:|---:|---:|
| 30 m | 69,738 dB | −72,738 dBm | 21,262 dB | 12,262 dB | 9,262 dB |
| 100 m, opcional | 80,196 dB | −83,196 dBm | 10,804 dB | 1,804 dB | −1,196 dB |

Los resultados se reproducen con este fragmento Python, sin dependencias:

```python
from math import log10, pi
for d in (30, 100):
    loss = 20 * log10(4 * pi * d * 2440e6 / 299792458)
    pr = -loss - 3
    print(d, loss, pr, [pr - s for s in (-94, -85, -82)])
```

Las sensibilidades son las del chip «+» a BER 0,1 %, no una garantía de archivos sin error. Los 3 dB supuestos no cubren estadísticamente desvanecimiento. Interferencia, suelo, obstáculos y orientación pueden cambiar el resultado. Repetiremos el presupuesto en ambas direcciones, incluido ACK, cuando conozcamos módulo y antenas; no sumaremos PA dos veces si la potencia ya incluye su ganancia. [Nordic N](fuentes.md)

## Tiempo y sobrecarga

Un raster de 320×240 a 8 bits ocupa 76 800 bytes, sin encabezado BMP/PGM. Requeriría al menos 1280 B/s para recorrerlo en 60 s dedicados solo al envío. La transferencia real debe dejar tiempo para preparación, guardado y pantalla.

Con 24 bytes de datos por carga de 32 se necesitan 3200 paquetes. Suponiendo dirección de 5 bytes, CRC de 2 y ACK vacío, los campos RF y ACK elevan el tráfico a 160 800 bytes equivalentes. El control RF tiene 9 bits: se trata de bits/8, no de paquetes alineados a bytes.

Para reproducir ese escenario y el efecto de latencia del host:

```python
from math import ceil
n = ceil(76800 / 24)
rf = 8 + 40 + 9 + 16  # preámbulo, dirección, control, CRC
bits = n * (rf + 32 * 8 + rf)  # DATA y ACK vacío
air = bits / 1e6
print(n, bits / 8, air, 1 - 76800 / (bits / 8))
for host_s in (0.002, 0.010):
    print(air + n * (2 * 130e-6 + host_s))
```

A 1 Mbit/s son 1,2864 s de emisión. Si suponemos dos cambios de modo de 130 µs y 2 ms del host por intercambio, resultan 8,5184 s; con 10 ms, 34,1184 s. No incluyen reintentos, control por bloques ni procesamiento de imagen: no son tiempos medidos ni una predicción del total.

La sobrecarga RF de este escenario es 52,239 %; original/carga radio es 0,75 antes de comprimir. El objetivo opcional de menos de 20 % sigue sin resolverse y depende también de acordar la capa de medición. Subir la tasa no reduce esa proporción.
