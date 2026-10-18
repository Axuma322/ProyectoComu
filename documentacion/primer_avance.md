# Primer avance: transmisión inalámbrica

IE0527 Ingeniería de Comunicaciones — UCR. Revisión: 17 de octubre de 2026.

## Qué vamos a construir

Usaremos una Raspberry Pi Zero y un radio nRF24 en cada extremo. El transmisor leerá una imagen almacenada y la enviará por paquetes; el receptor deberá reunirlos, comprobar el archivo, guardarlo y mostrarlo. La codificación de fuente se incorporará más adelante.

Según la consigna revisada, el enlace debe funcionar a 30 m con línea de vista, sin WiFi, Bluetooth/BLE, Zigbee, LoRaWAN ni redes celulares. Cada dispositivo tendrá alimentación autónoma, inicio mediante botón o interruptor y señalización luminosa, con un máximo de un módulo con microprocesador programable por extremo. El receptor permanecerá escuchando sin conocer cuándo empieza el envío.

Las imágenes serán BMP o PGM en gris, de hasta 320×240 píxeles. La prueba mínima pide reconstruir al menos dos de tres imágenes, conservar identidad exacta en modo sin pérdidas y superar 25 dB de PSNR en modo con pérdidas. Trabajaremos provisionalmente con el límite más estricto de 60 s desde el botón hasta el despliegue; debemos confirmar esa interpretación con el profesor. La consigna ya no está incluida en esta versión del repositorio. [Fuente C](investigacion/fuentes.md)

## Por qué elegimos nRF24

Elegimos esta opción para aprovechar las Pi y los radios que existen en el laboratorio. La biblioteca RF24 permite controlarlos por SPI sin incorporar una pila de red completa. También investigamos CC1101 y un enlace óptico/IR, pero implicarían hardware y trabajo adicional que todavía no hemos justificado. La [comparación](investigacion/alternativas.md) resume esas diferencias.

Nos falta confirmar si los radios son nRF24L01, nRF24L01+ o compatibles, y si incorporan PA/LNA. La fotografía de un conector de antena no resuelve esa identificación. El [inventario](hardware/inventario.md) conserva las observaciones previas y lo que debemos comprobar.

## Cómo planteamos la comunicación

La Pi preparará los datos y los pasará al radio mediante RF24. Enhanced ShockBurst se encargará del paquete de radio, su CRC, el ACK y los reintentos configurados. Nuestro programa deberá añadir identificación de transferencia, numeración de fragmentos y comprobación del archivo completo.

Un ACK de radio no demuestra que Linux haya procesado o guardado los datos. Por eso proponemos confirmar bloques desde la aplicación y verificar longitud y CRC del archivo antes de anunciar éxito. El [protocolo](../transmision/protocolo/README.md) describe el recorrido, los mensajes y la recuperación ante fallos.

La conexión inicial está en [hardware](hardware/README.md). Empezaremos estudiando 1 Mbit/s; 250 kbit/s solo será opción si confirmamos la variante «+». La tasa nominal no equivale a velocidad útil: intervienen cabeceras, ACK, reintentos, SPI y tiempos del programa. [Detalles del nRF24 y RF24](investigacion/nrf24.md)

## Qué necesitamos comprobar

Primero identificaremos y probaremos las plataformas, radios, antenas y alimentación existentes. Después ejecutaremos un ejemplo oficial de ida y vuelta, enviaremos datos conocidos y probaremos bloques y archivos sin compresión. Solo entonces mediremos distancia y tiempo con imágenes. El plan está al final del [protocolo](../transmision/protocolo/README.md#pruebas-iniciales).

Registraremos bytes enviados, cabeceras, repeticiones, tiempos y errores. El descarte de paquetes con CRC incorrecto impide medir directamente BER físico desde el funcionamiento normal del nRF24. Debemos consultar si se acepta reportarlo como no disponible junto con errores de paquete, reintentos y errores residuales de los datos recibidos; no son métricas equivalentes.

También falta resolver la pantalla y su alimentación, comprobar autonomía y fijar la configuración permitida para el módulo y su antena. El [presupuesto de enlace](investigacion/normativa_enlace.md) es un cálculo hipotético, no una prueba de alcance. La revisión normativa conserva las fuentes consultadas y los puntos pendientes.

Antes de programar el protocolo propio debemos cerrar modelo de hardware, alimentación, sistema operativo y backend de RF24. Mantendremos los parámetros de paquetes y espera como propuestas hasta medirlos. Las [fuentes](investigacion/fuentes.md) permiten distinguir datos de fabricante de nuestras decisiones.
