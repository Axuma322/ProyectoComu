# Normativa costarricense y presupuesto preliminar

Fecha de revisión: 2026-10-16. Fuentes: [SCIJ/PGR L, reforma oficial L26, SUTEL S, UIT U y Nordic N](fuentes.md). Este estudio no acredita conformidad de un módulo cuya referencia todavía se desconoce.

## Identificación normativa

El PNAF base es decreto 44010-MICITT. Se localizó en SCIJ el texto inicial; la copia completa MICITT consultada está fechada 7 de enero de 2026 y no basta para resolver vigencia al día de consulta. Se verificó además el decreto 45769-MICITT, publicado el 29 de abril de 2026, que reforma artículos y apéndices del PNAF. La Gaceta, pp. 73–75 del PDF, contiene tabla 22 y condiciones de antena actualizadas. [L, L26](fuentes.md)

| Candidato | Referencia en tabla 22 reformada | Consecuencia preliminar |
|---|---|---|
| nRF24 en 2400–2500 MHz | Salida máxima 30 dBm; PIRE máxima 36 dBm | Son techos regulatorios, no valores de configuración recomendados; módulo/antena deben comprobarse |
| CC1101 en 433,05–434,79 MHz | Salida 24 dBm; PIRE 30 dBm | La banda estrecha exige verificar ancho ocupado y espurias del perfil elegido |
| CC1101 en 902–915 MHz | Salida 24 dBm; PIRE 30 dBm | Candidato separado de 433 MHz; requiere módulo y antena para esa banda |
| CC1101 en 915–921 MHz | Tabla contempla 30/36 dBm y mención a transmisión inalámbrica de potencia | No adoptar esta fila para datos sin confirmar clasificación/aplicabilidad con SUTEL |
| CC1101 en 921–928 MHz | Dentro de fila 921–960: 24/30 dBm | Capacidad de sintonía del chip no implica certificación del módulo |

La reforma mantiene regla especial para enlaces **fijos** punto a punto de 2400–2500 MHz con antenas mayores de 6 dBi: reducción de salida de 1 dB por cada 3 dBi adicionales. No asumir que un prototipo portátil califica para esa excepción. No se adoptan 868 MHz ni límites FCC/CE como autorización costarricense. [L26](https://www.imprentanacional.go.cr/pub/2026/04/29/ALCA45_29_04_2026.pdf)

Las condiciones generales incluyen no causar interferencias perjudiciales, no reclamar protección y suspender emisión si se ocasiona interferencia. SUTEL publica RCS-245-2023 para homologación en bandas libres. Antes de pruebas radiadas, el responsable técnico del laboratorio debe verificar fabricante/modelo, certificado, potencia conducida, ganancia de antena, pérdidas de cable, ancho de banda, espurias y cambios permitidos de antena. [L, S](fuentes.md)

Pendiente normativo explícito: obtener texto consolidado vigente de SCIJ, descartar reformas posteriores a abril que afecten estas filas y confirmar con laboratorio/SUTEL el procedimiento aplicable a un prototipo académico. No se presume exención por uso universitario ni se declara legal la configuración solo por ser ISM. Esta incertidumbre no impide el diseño documental, pero debe resolverse antes de fijar parámetros radiados.

## Modelo reproducible a 30 m

Según [UIT-R P.525-5](https://www.itu.int/rec/R-REC-P.525-5-202411-I/en), usar propagación en espacio libre:

```text
Lfs = 20 log10(4 pi d f / c)          [d en m, f en Hz]
Pr = Pt + Gt + Gr - Lfs - Ladicional [dBm / dB]
M = Pr - Sensibilidad               [dB]
PIRE = Pt + Gt - Lcable_TX           [dBm]
```

El script [calculos_preliminares.py](calculos_preliminares.py) emplea c exacta y reproduce todas las cifras de este apartado. Escenario **hipotético sin PA**: 2440 MHz, Pt=0 dBm, antenas de 0 dBi, pérdidas adicionales conjuntas de 3 dB para cables/orientación/montaje. No se conocen ganancias ni pérdidas reales; tampoco se ha seleccionado canal legal definitivo.

| Distancia hipotética | Espacio libre | Pr | Margen a 250 kbit/s | Margen a 1 Mbit/s | Margen a 2 Mbit/s |
|---|---:|---:|---:|---:|---:|
| 30 m | 69,738 dB | −72,738 dBm | 21,262 dB | 12,262 dB | 9,262 dB |
| 100 m, opcional | 80,196 dB | −83,196 dBm | 10,804 dB | 1,804 dB | −1,196 dB |

Sensibilidades de chip de N a BER 0,1 %, no umbrales de transferencia de archivo sin errores. El margen no garantiza tiempo ni fiabilidad: interferencia, suelo, Fresnel, multitrayecto, alimentación y ACK de retorno pueden dominar. Los 3 dB supuestos no constituyen margen estadístico de desvanecimiento. Repetir presupuesto en ambas direcciones al conocer PA/LNA, antenas y potencia efectiva; no sumar ganancia de PA a una potencia que ya la incluya.

## Viabilidad temporal, sin promesas de rendimiento

El raster máximo de 8 bits contiene 76 800 bytes, antes de encabezados BMP/PGM. Como límite inferior, requiere 1280 B/s de imagen original para 60 s si todo ese tiempo se destinara a transferir. El presupuesto real debe reservar lectura, compresión, negociación, reconstrucción, guardado y pantalla.

Escenario del script: carga radio fija 32 bytes, cabecera de aplicación supuesta 8 bytes, datos 24 bytes, dirección 5 bytes, CRC 2 bytes y ACK vacío. Resultan 3200 paquetes para el raster; sumando campos RF y ACK, 160 800 bytes equivalentes de aire (control RF de 9 bits impide tratarlos como bytes físicos enteros por paquete). A 1 Mbit/s el tiempo de emisión de datos+ACK es 1,2864 s; añadiendo dos cambios de modo supuestos de 130 µs por intercambio y latencia host de 2 ms/paquete, 8,5184 s. A 10 ms/paquete serían 34,1184 s. Son escenarios parciales sin reintentos ni control por bloques; **no son tiempo total previsto ni medido**.

Con ese diseño, la sobrecarga RF mínima calculada es 52,239 % y la razón original/carga radio es 0,75 antes de comprimir: es normal que el transporte sin compresión aumente tamaño. El objetivo opcional de sobrecarga menor de 20 % no está resuelto; requiere acordar capa de medición y revisar cabeceras, ACK, agregación y retransmisiones. Aumentar tasa nominal no reduce esa proporción. No confundir compresión del códec con razón efectiva de transferencia definida en la consigna.
