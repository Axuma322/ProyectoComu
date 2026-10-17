# Alternativas de comunicación

Propuesta propia basada en [C, N, R, T, V y L26](fuentes.md). Ningún alcance ha sido medido. La plataforma común sería una Pi por extremo: la radio o el circuito óptico no agrega un segundo módulo con procesador programable.

| Aspecto | A: Pi Zero + nRF24L01+ | B: Pi Zero + CC1101 | C: Pi + óptica/IR de bajo nivel |
|---|---|---|---|
| Banda / modulación | Chip 2400–2525 MHz, GFSK; seleccionar subbanda autorizada | Chip 300–348, 387–464, 779–928 MHz; 2/4-FSK, GFSK, MSK, ASK/OOK | LED IR, fotodiodo, amplificador y comparador; OOK propuesta |
| Velocidad nominal | 250 kbit/s, 1 o 2 Mbit/s; original sin «+» no ofrece 250 kbit/s | 0,6–600 kbit/s; sensibilidad depende fuertemente de configuración | Sin valor cerrado: depende del emisor, detector, electrónica y temporización; portadora IR no equivale a tasa útil |
| Alcance | 30 m es objetivo por validar, sensible a interferencia, antenas y orientación | Menor pérdida de espacio libre a igual distancia/frecuencia menor es favorable; no garantiza alcance | 30 m exige diseño óptico y alineación; luz solar, oclusión y movimiento afectan |
| Desarrollo | Medio: SPI y RF24; fragmentación, integridad y control propios | Medio/alto: perfiles RF, filtro, antena para banda específica y protocolo propio | Alto: enlace bidireccional para confirmaciones, acondicionamiento y emisión temporizada |
| Energía | Chip TX 11,3 mA a 0 dBm; PA/LNA y Pi elevan consumo | Ficha: RX 14,7 mA a 1,2 kBaud/868 MHz; TX depende de potencia | Corriente pulsada del LED y receptor por dimensionar; medir sistema completo |
| Disponibilidad | Equipo confirma existencia física de componentes fotografiados; identificar variantes y contar/probar conjuntos | No confirmado en inventario | No se confirman pares ópticos adecuados |
| Compatibilidad | SPI + Enhanced ShockBurst no implementa WiFi/TCP; RF24 solo como driver | Radio de bajo nivel compatible conceptualmente, no Zigbee | Compatible conceptualmente; sin protocolos completos de red |
| Riesgos | Variante, alimentación, FIFO, Linux y medición BER | Regulación local separada, selección de banda/antena, tiempo útil a tasas bajas | Temporización Linux, saturación, velocidad, seguridad óptica y mecánica |
| Fuentes | N, R, RL, RI, P | T, L26 | V; diseño del circuito pendiente |

CC1101 incluye FIFOs TX/RX de 64 bytes, CRC y CCA configurables; no suministra por sí solo la transferencia fiable de archivos. El valor −116 dBm de TI corresponde a 0,6 kBaud/433 MHz/1 % PER: no debe emplearse en el presupuesto de un enlace de alta tasa. Su alimentación es 1,8–3,6 V según ficha; comprobar placa comercial. Las bandas 433 y 902–915 MHz se analizan separadamente en [normativa](normativa_enlace.md); no se propone 868 MHz por costumbre europea.

En óptica, las notas Vishay identifican dependencia con intensidad radiante, sensibilidad y luz ambiente. Un receptor de control remoto puede imponer ráfagas y pausas incompatibles con un flujo continuo: seleccionar receptor de datos o diseñar fotodiodo y amplificador. La opción no tiene velocidad ni autonomía presupuestadas; no puede declararse equivalente al radio sin prototipo.

Se recomienda A para aprovechar prioritariamente las plataformas Zero y radios existentes en el laboratorio, además de SPI y soporte RF24. Consultar el [inventario visual](../hardware/inventario.md) y las opciones de préstamo antes de proponer compras. Empezar conceptualmente a 1 Mbit/s, evaluar 250 kbit/s solamente si se confirma «+» y comparar 2 Mbit/s cuando el margen lo permita. No comprar PA/LNA para compensar un problema de alimentación o configuración. B queda como respaldo si el enlace de A falla tras diagnóstico; C exige más diseño electrónico y mecánico para esta primera demostración.
