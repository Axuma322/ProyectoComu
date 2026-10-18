# Fuentes de la investigación

Fuentes consultadas el 16 de octubre de 2026. Esta revisión de redacción no repite la búsqueda técnica ni certifica vigencia normativa al día de hoy.

| ID | Documento y acceso | Uso / límite de verificación |
|---|---|---|
| C | Consigna UCR, *Transmisión inalámbrica de imágenes con codificación de fuente*, pp. 1–8 | Revisada en la etapa inicial; el PDF fue retirado del repositorio y no está disponible en esta versión |
| N | Nordic Semiconductor, *nRF24L01+ Product Specification*, v1.0, septiembre 2008. [Portal oficial](https://docs.nordicsemi.com/bundle/nRF24L01P_PS_v1.0/resource/nRF24L01P_PS_v1.0.pdf); [copia del documento del fabricante alojada por SparkFun](https://www.sparkfun.com/datasheets/Wireless/Nordic/nRF24L01P_Product_Specification_1_0.pdf) | Portal redirige y descarga bloqueada; copia de 78 páginas leída para parámetros, §§5–8 y registros. No confundir con nRF24L01 sin «+» |
| R | [RF24 documentación oficial](https://nrf24.github.io/RF24/) | Controlador de bajo nivel; versión observada 1.6.2, no instalada |
| RL | [RF24 Linux/Raspberry Pi](https://nrf24.github.io/RF24/md_docs_2rpi__general.html) | SPI, GPIO, backend Linux |
| RI | [RF24 problemas comunes](https://nrf24.github.io/RF24/md_COMMON__ISSUES.html) | Alimentación, ACK y configuración compartida |
| RE | [RF24 ejemplos](https://nrf24.github.io/RF24/examples.html), [fuentes Linux](https://github.com/nRF24/RF24/tree/master/examples_linux) | Base para futura prueba, no ejecutados |
| RP | [pyRF24 oficial](https://github.com/nRF24/pyRF24) | Envoltura Python, advertencia de alimentación PA/LNA |
| P | [Raspberry Pi, modelos Zero](https://www.raspberrypi.com/documentation/computers/zero.html) | Plataforma, puertos y variantes; no identifica la placa fotografiada |
| T | [Texas Instruments CC1101](https://www.ti.com/product/CC1101), ficha Rev. I enlazada desde producto | Bandas, velocidad, SPI y consumo bajo condiciones especificadas |
| V | Vishay, [General Overview of IR Transmission in Free Ambient](https://www.vishay.com/docs/80073/general.pdf), [TSDP Receiver Series for Infrared Data Communications](https://www.vishay.com/docs/82666/tsdpreceiver.pdf) | Geometría, ruido óptico y receptor adecuado para datos |
| U | [UIT-R P.525-5, noviembre 2024](https://www.itu.int/rec/R-REC-P.525-5-202411-I/en) | Referencia de pérdidas en espacio libre; no modelo de obstáculos |
| L | [SCIJ/PGR, decreto 44010-MICITT](https://www.pgrweb.go.cr/DOCS/NORMAS/1/VIGENTE/D/2020-2029/2020-2024/2023/184DF/15C730.HTML); [texto completo alojado por MICITT](https://www.micitt.go.cr/sites/default/files/marco_juridico_legal/10.%20Decreto%20Ejecutivo%20N%C2%B0%2044010-MICITT%20Plan%20Nacional%20de%20Atribuci%C3%B3n%20de%20Frecuencias%20%28PNAF%29.pdf) | Texto base consultado; copia MICITT generada el 7 de enero de 2026, anterior a reforma de abril |
| L26 | [La Gaceta, Alcance 45, 29 abril 2026, decreto 45769-MICITT](https://www.imprentanacional.go.cr/pub/2026/04/29/ALCA45_29_04_2026.pdf), pp. 21–75, especialmente 73–75 | Reforma del PNAF; revisar Apéndice V, tabla 22. No se afirma haber descartado toda reforma posterior |
| S | [SUTEL RCS-245-2023, homologación en bandas libres](https://sutel.go.cr/pagina/procedimiento-de-solicitud-de-homologacion-de-dispositivos-que-operan-en-las-bandas-de-uso), [consulta de equipos](https://homologacion.sutel.go.cr/) | Procedimiento localizado; no se ha verificado certificado del módulo ni aplicabilidad concreta al prototipo universitario |

Los ejemplos RF24 se consultaron, pero no se ejecutaron. Para Nordic usamos la copia del documento del fabricante alojada por SparkFun porque la descarga oficial estaba bloqueada. No hemos comprobado homologación de un módulo concreto ni descartado reformas posteriores a las referencias regulatorias citadas.
