# Alternativas de transmisión

Investigamos tres opciones de bajo nivel. Usaremos Pi Zero con nRF24 para aprovechar el hardware del laboratorio; las otras quedan como respaldo si encontramos una limitación que no podamos resolver.

| Aspecto | Pi Zero + nRF24L01+ | Pi Zero + CC1101 | Pi + óptica/IR |
|---|---|---|---|
| Banda y modulación | Chip: 2400–2525 MHz, GFSK; elegir frecuencia permitida | Chip: 300–348, 387–464 y 779–928 MHz; FSK/GFSK, MSK y ASK/OOK | LED y detector; OOK como propuesta |
| Velocidad nominal | 250 kbit/s, 1 o 2 Mbit/s; 250 solo en «+» | 0,6–600 kbit/s | Depende del emisor, receptor y electrónica; sin valor definido |
| Alcance y limitaciones | 30 m por comprobar; afectan interferencia, antena y alimentación | Menor pérdida en espacio libre a frecuencia menor, con iguales ganancias; no garantiza alcance | Exige alineación; afectan luz ambiente, obstáculos y movimiento |
| Desarrollo | SPI y RF24; protocolo de archivos propio | SPI, configuración RF y protocolo propio | Circuito óptico, temporización y canal de retorno para ACK |
| Energía de referencia | Chip: TX 11,3 mA a 0 dBm; el PA/LNA y la Pi se presupuestan aparte | RX 14,7 mA a 1,2 kBaud/868 MHz, según TI; TX depende de potencia | Consumo del emisor y detector por dimensionar |
| Disponibilidad | Familias presentes; contar e identificar módulos | No confirmado | No se confirmó un par óptico adecuado |
| Principal riesgo | Variante, estabilidad eléctrica y tasa útil en Linux | Banda local, antena y perfil RF | Alcance/velocidad sin diseño validado |
| Fuentes | N, R, P | T, L26 | V |

Las tres opciones encajan conceptualmente con una comunicación de bajo nivel y una Pi por extremo; deben comprobarse configuración y hardware. [Fuentes de la tabla](fuentes.md)

El CC1101 ofrece CRC, FIFOs de 64 bytes y CCA configurables, pero no resuelve por sí solo el envío fiable de archivos. Su mejor sensibilidad publicada, −116 dBm, corresponde a 0,6 kBaud en 433 MHz y 1 % PER; no sirve como presupuesto de alta tasa. Las bandas propuestas se revisan por separado en [normativa](normativa_enlace.md): no tomamos 868 MHz como autorización local.

En IR, un receptor de control remoto puede imponer pausas incompatibles con datos continuos. Haría falta un receptor de datos adecuado o diseñar la electrónica, además de comprobar alineación y luz ambiente. La frecuencia de portadora no equivale a tasa de datos.

La opción nRF24 requiere menos hardware adicional y tiene ejemplos RF24 para Linux. Empezaremos estudiando 1 Mbit/s y compararemos otras tasas después de identificar el chip y medir el enlace. Antes de comprar radios o amplificadores, revisaremos el [inventario](../hardware/inventario.md) y diagnosticaremos alimentación y configuración.
