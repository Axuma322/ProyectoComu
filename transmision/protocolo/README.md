# Protocolo implementado de imágenes

Código: `transmision/archivos.py` y `transmision/enlace.py`; integración:
`integracion/enlace.py`. Es **stop-and-wait**, con una trama y su confirmación
de aplicación en vuelo. Las ventanas y BLOCK_ACK del
[diseño preliminar](../../documentacion/investigacion/protocolo_preliminar.md)
no están implementados.

## Trama de 32 bytes

Cabecera `struct.Struct('>BBIH')`: enteros sin signo en big-endian.

| Bytes | Campo | Valor |
|---|---|---|
| 0 | Identificador de formato | `0xC1` |
| 1 | Tipo | START=1, DATA=2, FIN=3, ACK=4 |
| 2–5 | Sesión | Entero aleatorio de 32 bits generado por TX |
| 6–7 | Índice | Fragmento DATA; cero en START/FIN |
| 8–31 | Cuerpo | Hasta 24 bytes, rellenados con ceros |

| Tipo | Cuerpo |
|---|---|
| START | Longitud total del flujo y CRC-32: dos enteros de 32 bits |
| DATA | Siguiente bloque de hasta 24 bytes del flujo |
| FIN | Ceros; solicita validación y publicación final |
| ACK | Tipo confirmado y estado en los primeros dos bytes; resto cero |

ACK repite sesión e índice. Estado 0 significa aceptación; 1, rechazo de
parámetros, fragmento o archivo; 2, receptor ocupado por otra sesión al recibir
START. TX solo acepta ACK coincidente en tipo, sesión, índice y tipo confirmado.

## Flujo transportado

`integracion.enlace.make_wire` concatena longitud del JSON (4 bytes big-endian),
metadatos JSON UTF-8 y archivo codificado HUF2 o QPG1. El límite es **256 KiB en
total** y 4096 bytes de JSON. START describe ese flujo completo, no solo los
bytes del códec. La longitud permite recortar el relleno del último fragmento.

Los metadatos contienen modo, bits, dimensiones, tamaños, hashes, métricas de
preparación/calidad medidas en TX e identificador de trabajo. Viajan por el
mismo radio; no existe un canal TCP auxiliar para completarlos.

## Confirmación y errores

1. START acepta una sesión si los tamaños son válidos y RX está disponible.
2. DATA se guarda por índice. Repetirlo no duplica bytes ni progreso; un mismo
   índice con contenido diferente se rechaza. START repetido no borra lo recibido.
3. FIN exige todos los fragmentos y CRC-32 correcto. El callback reconstruye,
   valida SHA-256/dimensiones y guarda imagen e historial.
4. Solo después se emite el ACK de FIN. Si se pierde, RX conserva el resultado
   de cierre 90 s y responde a FIN repetido sin reconstruir dos veces.

Se mantienen auto-ACK y CRC hardware de 16 bits. Son distintos del ACK de
aplicación: un `write()` exitoso no demuestra que RX haya guardado la imagen.
La limpieza de FIFO/IRQ antes de cada escritura bloqueante evita reutilizar
una trama o un evento TX_DS antiguos, fallo observado durante la integración.

Cada trama tiene un intento inicial y hasta cuatro repeticiones. La espera
de respuesta de aplicación es 0,4 s; FIN dispone de 3 s para reconstrucción.
El hardware usa `set_retries(5, 15)` por escritura. El adaptador vuelve a escucha
tras enviar; RX espera 3 ms antes de responder para permitir el cambio de TX.

**No hay plazo global implícito de 60 s.** `send_file` acepta un `deadline`
monotónico opcional para otros llamadores; el servicio de imágenes no lo pasa.
RX descarta una sesión tras 10 s de inactividad. Si faltan confirmaciones o RX
rechaza datos, TX registra fallo explícito. No existe reanudación tras reiniciar,
CANCEL de aplicación ni recuperación mediante mapas de bloques.

## Contadores y verificación

TX conserva resultados, incluso fallidos, con fragmentos/bytes confirmados,
ACK hardware presentes/ausentes, ACK de aplicación, respuestas ajenas, reintentos
y tiempos de escritura/espera. Reintentos no equivalen a reinicios. El total de
bytes de aplicación no incluye todo el tráfico físico de auto-ACK.

Huffman exige SHA-256 idéntico al original; con pérdidas exige el hash de la
reconstrucción calculada en TX. CRC y hashes detectan errores; no autentican al
emisor. Las tramas rechazadas por CRC no llegan al programa, así que BER físico
no se deriva de estos contadores.

`transmision/test_imagenes.py` comprueba corrupción, ACK perdidos, duplicados,
cierres únicos y avance de más de 60 s con reloj virtual. Los
[informes reales](../../documentacion/README.md) conservan la evidencia de radio.
