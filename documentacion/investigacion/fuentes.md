# Fuentes verificables

Consulta: 2026-10-16. Las referencias locales y oficiales sustentan los documentos; no se usaron publicaciones comerciales para prometer alcance.

| ID | Documento y acceso | Uso / límite de verificación |
|---|---|---|
| C | [Consigna local](../consigna/escenario_original.pdf), pp. 1–8 | Requisitos, evaluación y recursos; lectura completa |
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

El listado de ejemplos Linux se comprobó mediante API oficial de GitHub y sus fuentes se consultaron en el servidor raw; la página web del directorio no fue recuperable por el navegador de investigación. No se compiló ningún ejemplo ni se consultó un modelo específico en el registro de homologación. La descarga Nordic presentó el bloqueo indicado; su copia documental se obtuvo por SparkFun. La recomendación UIT también se verificó en su PDF en español, §2.3, ecuaciones 5–6. Conservar fecha, versión y URL al ampliar referencias. No se distribuyen fichas de terceros dentro del repositorio.
