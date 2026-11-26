# Prueba de campo a aproximadamente 25 metros

Reporte recibido del equipo el 26 de noviembre de 2026, después de actualizar
el software y solicitar la vuelta a los AP permanentes.

| Dato | Evidencia disponible |
|---|---|
| Distancia | Aproximadamente 25 m, comunicados por el equipo |
| Sin pérdidas | El equipo confirmó que funcionó |
| Con pérdidas | El equipo confirmó que funcionó |
| «10/10» | Valoración de funcionamiento satisfactorio; no diez intentos contabilizados |
| Tiempo y calidad | Descritos como buenos, sin valores exactos aportados |
| Contador de radio | Se comunicó una cifra cercana a 2000, descrita inicialmente como «reinicios» |

La interfaz implementada muestra **reintentos hardware** y **reintentos de
aplicación**, no un contador de reinicios del radio o de la Raspberry. Sin el
JSON de ese ensayo no se atribuye el valor aproximado a un campo concreto.
Los dB de la interfaz corresponden a **PSNR calculado en TX**, no a intensidad
de señal RF. La expresión «buen BCR» del reporte no identifica una medida ni
un valor verificable; no se registra como BER físico. El software no mide BER físico.

No se aportaron para esta ronda logs, identificación de trabajos, imágenes,
profundidad de bits, número de intentos, tiempos exactos, condiciones de línea
de vista ni datos de alimentación. No se deducen esos datos de las rondas
anteriores. Tampoco acredita todavía 30 m ni autonomía medida.

Para la siguiente ronda conviene guardar `resultados/<trabajo>.json` en TX y el
registro de `recepciones/<sesion>.json` en RX, junto con distancia, modo, bits,
alimentación y resultado por intento. Ver la [guía de operación](../../operacion.md).
