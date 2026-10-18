# Envío de datos por paquetes

La idea es construir un protocolo sencillo sobre RF24, con un transmisor de archivos y un receptor que permanece escuchando. Todavía no hemos fijado el formato binario ni implementado estas funciones. El radio aportará CRC, ACK y reintentos por paquete; nuestro programa controlará la transferencia completa. [Nordic y RF24](../../documentacion/investigacion/fuentes.md)

## Recorrido y estados

```mermaid
flowchart LR
  A[Archivo en Pi TX] --> B[Codificacion futura]
  B --> C[Metadatos y fragmentos]
  C --> D[RF24 y SPI]
  D --> E[Radio TX]
  E <-->|GFSK y ACK| F[Radio RX]
  F --> G[RF24 y SPI]
  G --> H[Validar y reunir fragmentos]
  H --> I[Descodificacion futura]
  I --> J[Guardar y mostrar en Pi RX]
```

Primero enviaremos archivos sin compresión. La futura codificación entregará un flujo de bytes con su modo, parámetros y tamaños; el protocolo transportará ese flujo sin depender del algoritmo.

TX pasará por **configurar → esperar botón → preparar → negociar → enviar → cerrar**. RX pasará por **configurar → escuchar → validar inicio → recibir → verificar → guardar y mostrar**. Ante fallo o cancelación, se registra el motivo, se descarta el archivo temporal y se vuelve a espera. Un nuevo intento usará otra identificación.

## Mensajes propuestos

| Mensaje | Función |
|---|---|
| START / META | Identificar sesión, versión, modo, formato/dimensiones, tamaños, fragmentación y CRC del flujo. Dividir metadatos si no caben en una carga |
| READY / REJECT | Aceptar o rechazar parámetros desde la aplicación antes de enviar datos |
| DATA | Llevar identificación de sesión, índice y fragmento |
| BLOCK_ACK / NACK | Confirmar fragmentos recibidos o indicar cuáles faltan |
| FIN | Solicitar cierre y comprobación de longitud y CRC completos |
| RESULT / RESULT_ACK | Confirmar resultado, guardado y despliegue; cerrar la sesión |
| CANCEL | Detener una transferencia con una razón |

Para los cálculos planteamos una cabecera DATA de 8 bytes: tipo/versión, banderas, sesión de 32 bits e índice de 16 bits. Quedarían 24 bytes de datos en una carga fija de 32. Es una propuesta revisable; falta fijar orden de bytes, límites y serialización. Los metadatos se validarán antes de reservar memoria.

La comprobación propuesta combina CRC de radio de dos bytes y CRC-32 del flujo completo. Para las pruebas compararemos también SHA-256 y bytes del archivo original frente al recibido. El CRC detecta errores accidentales; no autentica al emisor.

## Confirmaciones y recuperación

El acceso será semidúplex por turnos: TX enviará un bloque y cederá el medio a RX para una respuesta de aplicación. Mantendremos auto-ACK de radio por paquete. No suponemos CSMA/CA ni ausencia de interferencias.

Proponemos bloques de 16 fragmentos y un mapa de recepción para reenviar los ausentes. Al principio habrá una transacción de radio en vuelo para asociar sus contadores. Un fragmento duplicado se reconoce por sesión e índice y no se agrega dos veces. No mezclaremos sesiones; una petición ajena puede recibir BUSY.

Si se pierde READY, repetir START de la misma sesión no debe borrar el progreso. Si se pierde RESULT, TX repetirá FIN y RX devolverá el resultado guardado sin procesar otra vez el archivo. La caché de cierres debe durar más que la ventana de reintentos.

Los plazos iniciales son 1 s para READY, 0,5 s para respuesta de bloque, hasta tres reintentos de aplicación y 3 s de inactividad RX. Se ajustarán con pruebas. Cada reintento cuenta dentro del presupuesto total de 60 s desde el botón, incluido guardado y despliegue; no basta con limitar cada espera por separado. Los reintentos automáticos del radio se configuran aparte en [nRF24](../../documentacion/investigacion/nrf24.md).

## Pruebas iniciales

Empezaremos con el ejemplo oficial de ida y vuelta y cargas conocidas. Después enviaremos bloques, provocando pérdidas, duplicados, ACK perdido, cancelación y reinicio. El resultado aceptable será reconstrucción exacta o fallo explícito dentro del plazo, nunca éxito con datos incompletos.

Seguiremos con archivos sin compresión, incluyendo fragmento final parcial y tamaños inválidos. Comprobaremos longitud, bytes y SHA-256 antes de pasar a imágenes. Finalmente probaremos 30 m con línea de vista, receptor sin aviso de inicio y alimentación autónoma, conservando también los intentos fallidos.

Por intento registraremos configuración, imagen e identificación de sesión, bytes útiles/control/repetidos, fragmentos faltantes, reintentos hardware y de aplicación, MAX_RT, tiempos y estado final. Hay que leer ARC_CNT antes de otra transacción; PLOS_CNT es limitado y se reinicia al escribir canal, por lo que no sirve como acumulador general.

Usaremos reloj monotónico para intervalos locales. Para botón→pantalla necesitamos una base temporal común, por ejemplo vídeo; restar relojes independientes de las Pi no es válido. Botón→RESULT recibido en TX añade el retorno y puede registrarse como cota superior.

La cantidad exacta de tráfico RF, incluidos ACK no observados, requiere instrumentación o límites explícitos de estimación. Debemos acordar con el profesor la capa de contabilidad. También preguntaremos cómo reportar BER: las tramas descartadas por CRC no llegan al programa. PER, reintentos y BER residual de cargas entregadas no sustituyen BER físico; cero errores después de CRC no prueba un canal sin errores.
