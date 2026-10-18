# Comunicación con nRF24 y RF24

El nRF24 es nuestra opción para comunicar las Pi. Aún debemos identificar los módulos del laboratorio. Los datos siguientes corresponden al **nRF24L01+** de Nordic, no a una placa comercial ya verificada. [Especificación N](fuentes.md)

## Qué ofrece el radio

| Característica del chip «+» | Dato de referencia |
|---|---|
| Modulación y frecuencia | GFSK; centro = 2400 + RF_CH MHz, canales 0–125 |
| Tasa / sensibilidad a BER 0,1 % | 250 kbit/s / −94 dBm; 1 Mbit/s / −85 dBm; 2 Mbit/s / −82 dBm |
| Potencia configurable | −18, −12, −6 y 0 dBm |
| Alimentación | 1,9–3,6 V; planteamos 3,3 V |
| Corriente típica | TX: 11,3 mA a 0 dBm; RX: 12,6/13,1/13,5 mA a las tasas anteriores |
| SPI | Hasta 10 Mbit/s; CE controla modo e IRQ indica eventos |
| Carga útil y FIFO | Hasta 32 bytes por paquete; tres cargas en cada FIFO TX/RX |
| Paquete ESB | Preámbulo de 1 byte, dirección de 3–5 bytes, control de 9 bits, carga de 0–32 bytes y CRC de 1–2 bytes |

GFSK transmite símbolos mediante cambios de frecuencia con filtrado gaussiano. A menor tasa mejora la sensibilidad, pero aumenta el tiempo de emisión. A 2 Mbit/s se necesitan centros separados al menos 2 MHz para canales no solapados. Los canales configurables no son todos necesariamente utilizables bajo la normativa local.

Enhanced ShockBurst (ESB) añade CRC, ACK automático y reintentos. El campo de control contiene longitud, PID y NO_ACK; PID/CRC ayudan a detectar duplicados de radio. Nuestro programa sigue necesitando numeración e integridad del archivo. Un ACK confirma recepción por el radio, no guardado por Linux.

El chip no implementa CSMA/CA para nuestra propuesta. RPD indica energía sobre un umbral; no mide BER ni asegura que el canal esté libre. En funcionamiento normal, el CRC descarta paquetes dañados antes de entregarlos al host: reintentos y errores de paquete no equivalen a BER físico. [N](fuentes.md)

## Configuración inicial

Ambos extremos deberán coincidir en canal, tasa, dirección y su longitud, CRC, auto-ACK y tamaño fijo o dinámico de carga. Proponemos dirección de cinco bytes, CRC de dos y carga fija de 32 bytes. El relleno se cuenta como tráfico, pero no forma parte del archivo.

Al iniciar comprobaremos SPI y registros, limpiaremos FIFO e indicadores y aplicaremos la configuración explícitamente. RX quedará escuchando; START/READY coordinará la transferencia desde la aplicación. No hace falta sincronizar relojes para recibir paquetes.

Como punto inicial proponemos ARD de 1500 µs y cinco reintentos automáticos con ACK vacío. El chip admite 0–15 reintentos y ARD de 250–4000 µs; a 250 kbit/s se requieren al menos 500 µs. Un ACK con carga obliga a revisar su duración. Al alcanzar MAX_RT, el programa debe atender el evento y decidir si repite o cancela, con un límite. Estos valores todavía deben probarse.

Si el chip es nRF24L01 sin «+», no podremos usar 250 kbit/s. Una placa PA/LNA tendrá consumo y potencia propios: el conector de antena no demuestra esa variante. La [conexión y alimentación](../hardware/README.md) se confirmarán con su ficha.

## Biblioteca y primeras pruebas

Planteamos C++ con **RF24** para el bucle de transmisión; **pyRF24** queda como alternativa para instrumentación. RF24 controla SPI/GPIO y registros, sin implementar archivos ni codificación. Elegiremos versión y backend según modelo de Pi, kernel y arquitectura del sistema. En Linux deben comprobarse permisos, dispositivo `/dev/spidevA.B` y numeración BCM. [RL y RP](fuentes.md)

Revisamos los ejemplos oficiales `examples_linux/gettingstarted.cpp`, `acknowledgementPayloads.cpp` y `streamingData.cpp`, pero no los hemos compilado ni ejecutado. Empezaremos con ida y vuelta y lectura de configuración; después evaluaremos envío continuo. [Ejemplos oficiales](https://github.com/nRF24/RF24/tree/master/examples_linux)

Que `begin()` responda bien solo comprueba comunicación con el radio. Sin auto-ACK, un `write()` exitoso tampoco prueba recepción remota. Linux puede retrasar el vaciado de FIFO, SPI o escritura a disco, por lo que mediremos tasa útil antes de elegir el envío definitivo. [Problemas comunes](https://nrf24.github.io/RF24/md_COMMON__ISSUES.html)

No usaremos RF24Network, RF24Mesh, RF24Gateway ni TCP/IP. Sobre el driver planteamos nuestro [protocolo punto a punto](../../transmision/protocolo/README.md).
