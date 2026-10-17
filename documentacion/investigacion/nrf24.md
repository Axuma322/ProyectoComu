# nRF24L01+ y biblioteca RF24

Referencia principal: [Nordic N](fuentes.md), §§5–8; conexión y software: [RL, RI, RE y RP](fuentes.md). Los parámetros siguientes pertenecen al chip **«+»**, no al módulo fotografiado.

## Radio y paquete

| Propiedad del chip | Valor / función |
|---|---|
| Modulación | GFSK: filtrado gaussiano de los símbolos antes de desplazar frecuencia; no OFDM |
| Frecuencia central | 2400 + RF_CH MHz; RF_CH válido 0–125; 126 canales configurables, no todos utilizables legalmente |
| Tasa / sensibilidad a BER 0,1 % | 250 kbit/s / −94 dBm; 1 Mbit/s / −85 dBm; 2 Mbit/s / −82 dBm |
| Potencia programable del chip | −18, −12, −6, 0 dBm |
| Alimentación / consumo típico | 1,9–3,6 V; TX 11,3 mA a 0 dBm; RX 12,6/13,1/13,5 mA según tasa ascendente |
| Interfaz | SPI hasta 10 Mbit/s, CE de control, IRQ activa baja |
| Carga útil / FIFO | Hasta 32 bytes; FIFOs TX/RX de tres cargas cada una |
| Paquete ESB | Preámbulo 1 byte, dirección 3–5 bytes, control 9 bits, carga 0–32 bytes, CRC 1–2 bytes |
| Control ESB | Longitud 6 bits, PID 2 bits, NO_ACK 1 bit |
| Confirmación | ACK automático y retransmisión configurables; MAX_RT señala agotamiento |

Enhanced ShockBurst (ESB) automatiza transacciones de radio; SPI carga datos, el hardware transmite, espera ACK y puede repetir. El CRC descarta paquetes dañados. PID/CRC ayudan a suprimir duplicados de radio, sin sustituir la numeración de fragmentos del archivo. [N](fuentes.md)

El ACK de radio solo confirma recepción por la radio: el proceso Linux podría no haber validado ni guardado datos. Por diseño propio, habrá confirmación de aplicación y verificación del flujo completo. No hay CSMA/CA automático en esta propuesta. RPD detecta energía sobre un umbral; no mide BER ni garantiza un canal libre.

Menor tasa ofrece más sensibilidad pero ocupa el medio más tiempo. Separación de centros no equivale a ancho ocupado: a 2 Mbit/s se necesitan al menos 2 MHz para canales no solapados. Seleccionar centro con margen a los bordes legales y emisiones verificadas. El protocolo empieza en un canal fijo acordado; no se implementará salto automático en esta etapa.

## Configuración compartida y secuencia propuesta

Antes de comunicar, ambos extremos deben acordar canal, tasa, dirección y anchura de dirección, CRC, auto-ACK y longitud fija/dinámica de carga. La potencia puede diferir, pero se presupuestan ida y retorno. Propuesta inicial: direcciones de cinco bytes, CRC de dos bytes y carga fija de 32 bytes; relleno excluido del archivo pero contado como tráfico.

Al arrancar: alimentar establemente, habilitar SPI, comprobar respuesta de registros, vaciar FIFO y limpiar indicadores, aplicar configuración explícita y registrar su lectura. El receptor entra en RX antes de esperar START. La sincronización de paquete la resuelve la radio; START/READY sincroniza la sesión de aplicación. No exige relojes de pared sincronizados.

Para ACK vacío se propone ARD de 1500 µs y hasta cinco retransmisiones automáticas como punto inicial conservador; son valores de diseño a ajustar, no mediciones. El chip permite 0–15 reintentos y ARD de 250–4000 µs. A 250 kbit/s debe respetarse al menos 500 µs; ACK con carga requiere comprobar su duración. MAX_RT debe atenderse, limpiar el estado y decidir reintento limitado o cancelación. No encadenar reintentos ilimitados.

## Software y límites

RF24 controla la radio; no implementa archivos ni codificación. Linux permite backend SPI/GPIO, con diferencias de permisos y numeración. [RL](https://nrf24.github.io/RF24/md_docs_2rpi__general.html) documenta `/dev/spidevA.B`, GPIO BCM y la API de dispositivo de caracteres. Elegir backend y fijar versión tras conocer placa, kernel y arquitectura del sistema operativo; no copiar instrucciones BCM2835 o paquetes binarios sin comprobar compatibilidad.

Plan de desarrollo: partir de los ejemplos oficiales Linux `examples_linux/gettingstarted.cpp`, `acknowledgementPayloads.cpp` y `streamingData.cpp`, localizados en [RE](https://github.com/nRF24/RF24/tree/master/examples_linux). Sus fuentes fueron consultadas, no compiladas ni ejecutadas; fijar versión antes de usarlas. La primera prueba debe consultar configuración y confirmar ida y vuelta. `begin()` exitoso prueba SPI, no el enlace; un `write()` sin auto-ACK no demuestra recepción. [RI](https://nrf24.github.io/RF24/md_COMMON__ISSUES.html)

Se propone C++ con RF24 para el bucle de transferencia por menor intermediación; Python/pyRF24 es alternativa para instrumentación y futura integración, su instalación debe probarse en la Pi real. No se agregan dependencias ahora. Linux no es de tiempo real: el vaciado de FIFO, cambios de dirección, SPI y escritura en disco pueden limitar la tasa; mantener almacenamiento lento fuera del bucle crítico cuando sea posible. [R, RP](fuentes.md)

RF24Network, Mesh, Gateway y TCP/IP no forman parte de la solución propuesta. La biblioteca no convierte el chip en WiFi ni añade PA/LNA. Una placa comercial con amplificador necesita ficha propia de ganancia, potencia y corriente; una antena externa por sí sola no confirma la variante. Para conexiones y desacoplamiento véase [hardware](../hardware/README.md).
