# Metodología de implementación y evaluación

Plan futuro, **ninguna prueba de radio ejecutada**. Fuentes: [consigna C, Nordic N y RF24 RI](../../documentacion/investigacion/fuentes.md). Los modelos analíticos se encuentran en [enlace](../../documentacion/investigacion/normativa_enlace.md).

## Validación escalonada

| Fase | Procedimiento previsto | Criterio de éxito / evidencia |
|---|---|---|
| 0. Inventario y electricidad | Confirmar dos conjuntos, fichas, OS, SPI, autonomía y normativa | Referencias registradas, tensiones verificadas durante actividad y configuración compatible |
| 1. Comunicación local | Ejemplo oficial de ida/vuelta, baja potencia y separación evitando saturación | Ambos extremos reciben cargas conocidas y configuración leída coincide; no basta `begin()` |
| 2. Datos de prueba | Secuencias conocidas con contador, patrones uniformes y pseudoaleatorios | Contadores y bytes coinciden; registrar huecos, duplicados, errores y reintentos por separado |
| 3. Bloques fiables | Inyectar pérdida, duplicación, ACK perdido, metadatos inválidos, timeout y cancelación | Reensamblado exacto o fallo explícito y acotado; ninguna sesión colgada ni falso éxito |
| 4. Archivos sin compresión | Diferentes longitudes, fragmento final parcial, archivo vacío de prueba, límite y exceso | Longitud y SHA-256 iguales; rechazo seguro de tamaños inválidos; retorno a escucha |
| 5. Imágenes iniciales | BMP/PGM válidos y corruptos; leer, enviar, guardar y mostrar sin códec | Raster y archivo preservados en ruta reversible; no mostrar parcial como éxito |
| 6. Codificación posterior | Integrar un modo sin pérdidas y uno con pérdidas; cuatro ajustes del segundo | Identidad exacta sin pérdidas; curva tasa-distorsión y costos de proceso con tres clases de imagen |
| 7. Distancia y desempeño | 30 m LOS; receptor sin hora de inicio; hasta tres intentos por imagen separados 5 min | Al menos dos de tres imágenes correctas, sin pérdidas exactas o con pérdidas reconocibles y PSNR >25 dB; total ≤60 s; todas las métricas reportadas |

Antes de la fase 7 se verifican batería, botones y señales. Para comparar tasas/códecs, usar mismos archivos y configuraciones documentadas; repetir condiciones, conservar intentos fallidos, indicar tamaño de muestra y dispersión. Imágenes oficiales aún no están entregadas. Generar o conseguir posteriormente controles fotográfico, uniforme y de detalle fino; no confundir fotografías de componentes con imágenes oficiales de evaluación.

## Definiciones e instrumentación

Un reloj monotónico por equipo mide intervalos. No restar marcas de dos relojes independientes sin sincronización. TX mide compresión y fase de transferencia; RX mide descodificación, escritura y despliegue, y devuelve intervalos/estado en RESULT. Para tiempo total desde botón hasta pantalla, preferir observación externa común (vídeo del botón y pantalla, o instrumento con base temporal común); botón→RESULT recibido en TX es una cota superior adicional que incluye retorno. No publicarla como intervalo exacto hasta despliegue.

| Métrica | Método y definición operativa propuesta |
|---|---|
| Tamaño original | Bytes del archivo BMP/PGM completo, incluidos encabezados; guardar además bytes del raster, dimensiones y profundidad |
| Tamaño codificado | Bytes del códec sin transporte, para separar eficiencia de fuente y enlace |
| Tamaño efectivamente transmitido | Libro de tráfico con cada intento DATA/META/control, relleno, cabeceras de aplicación, campos RF y ACK en ambas direcciones; reportar también bytes de carga radio. La tabla principal explicitará capa y convención acordada con docente |
| Razón de compresión | C: tamaño original / tamaño transmitido, incluyendo cabeceras y reintentos según convención. Añadir razón de códec original/codificado separadamente, no sustituirla |
| Sobrecarga | (Tráfico total − bytes codificados únicos entregados) / tráfico total; incluye metadatos, relleno, control, ACK, campos RF y duplicados/reintentos. Guardar desglose para otra interpretación docente |
| Tiempo compresión | Intervalo monotónico exclusivamente alrededor del codificador en TX; lectura separada |
| Tiempo transmisión | Desde inicio RF del primer START hasta última confirmación pertinente; registrar intervalo de pared de la fase y, aparte, suma de airtime modelada por tasa y tramas. Precisar qué confirmación cierra el flujo; no igualar suma de emisiones a duración de transferencia |
| Tiempo descompresión | Intervalo monotónico alrededor del descodificador RX |
| Tiempo total | Botón→imagen desplegada y guardada; definir callback de pantalla completada y contrastar con vídeo común |
| Tasa útil | Bytes originales / tiempo total, B/s; bits/s solo multiplicando por ocho explícitamente |
| BER | Véase limitación y consulta abajo; N/D si no medible, nunca reintentos/bits |
| PSNR | Raster original x y reconstruido y, misma geometría y escala: MSE = sum((x−y)^2)/(ancho×alto); PSNR=10 log10(MAX²/MSE), MAX=255 para 8 bits; MSE=0 implica infinito |
| SSIM opcional | Solo si se adopta: fijar versión, ventana, parámetros y rango dinámico; no se instala biblioteca ahora |

En modo sin pérdidas comprobar comparación byte a byte y SHA-256 del archivo, diferencia máxima del raster cero, MSE cero y PSNR infinito. En modo con pérdidas, el digest del flujo transportado debe coincidir aun cuando el raster sea distinto: error de radio no se acepta como «pérdida» del códec.

Para PSNR/SSIM, la referencia debe estar precargada en RX para evaluación identificada por digest, o calcularse en herramienta posterior con original y reconstrucción. Precargar referencias no permite sustituir los bytes recibidos por el original. Preguntar al docente si el reporte final puede completarse en herramienta de evaluación o si debe aparecer inmediatamente en ambos dispositivos. BER permanece pendiente de acuerdo, sin ocultarla de la tabla.

## BER, errores de paquete y observabilidad

BER físico = bits erróneos / bits observados con referencia en un punto definido del receptor. PER de primera transmisión = paquetes erróneos o perdidos / paquetes emitidos inicialmente; agotamiento de reintentos y tasa de entregas fallidas son métricas diferentes. Un reintento puede deberse a ACK perdido aunque el DATA se recibió. El CRC filtra tramas dañadas y el nRF24 no entrega al host el flujo bruto con todos los errores; no existe BER físico directamente observable en operación ESB normal.

Propuesta defendible: medir entrega de paquetes con secuencia conocida y contadores, registrar ARC_CNT por transacción antes de la siguiente, eventos MAX_RT y repeticiones de aplicación. PLOS_CNT es limitado/saturable y se reinicia al escribir canal: no usarlo como contador total de pérdidas. Distinguir reintentos hardware, intentos de aplicación y pérdidas observadas por RX. Para una prueba PER sin auto-ACK, acordar ventana y número esperado, y etiquetarla como ensayo diagnóstico separado del modo final.

Comparar bits de cargas entregadas permite BER residual **condicionada a recepción válida**, no BER del canal. Cero errores observados después de CRC y reintentos no demuestra BER físico cero. Desactivar CRC cambia el punto de medida y aún quedan pérdidas de sincronismo/dirección; no basta con dividir diferencias de bytes por bits originales. La estimación a partir de PER exigiría independencia de errores, longitud conocida y control de pérdidas no debidas a bits; no se propone como medición directa.

El total de tráfico RF tampoco es completamente observable solo con contadores TX: ACK perdidos y DATA no detectados introducen incertidumbre. Instrumentar ambos extremos, contar ACK emitidos cuando sea inferible por recepción válida y documentar límites; si se requiere conteo físico exacto, usar captura/instrumentación externa capaz de observar los paquetes. No etiquetar un cálculo con esos límites como bytes medidos exactos. En la fase inicial preferir una transacción en vuelo para poder asociar ARC_CNT al paquete.

Consulta técnica preparada: «Con nRF24L01+ y CRC/auto-ACK, las tramas erróneas no llegan al host. ¿Se acepta reportar BER físico como no disponible junto con PER, reintentos y BER residual condicionada? Si debe medirse BER físico, ¿qué instrumental o modo de prueba se autoriza? ¿La sobrecarga y tamaño transmitido incluyen campos RF y ACK o solo cargas de radio, y cómo debemos registrar ACK no observables?»

## Registro por intento y estudio futuro

Guardar JSON/CSV de resumen y log de eventos: ID de intento/sesión, imagen/digests, modo/algoritmo/parámetros, versión del software y RF24, placa y radio, canal/tasa/potencia/CRC/ARD/ARC, distancias, orientación/LOS/obstáculos, batería al inicio/final, tamaños, bytes por categoría/dirección, fragmentos únicos, duplicados, faltantes, reintentos, MAX_RT, marcas monotónicas, intervalos por etapa, estado final y causa de fallo. Incluir método/incertidumbre de cada métrica; valor N/D con razón cuando corresponda, no cero ficticio.

El estudio debe contestar C14–18: ahorro temporal frente a razón de compresión; umbral perceptible/inaceptable mediante comparación visual con criterio explícito; costo de códec que anula ahorro; recomendación y sensibilidad al tipo de imagen. Barrer cuatro puntos con pérdidas y baseline sin comprimir, comparar con modo sin pérdidas. Graficar PSNR frente a razón efectiva y tamaño codificado por cada imagen; medir sobre enlace real para objetivo opcional. Registrar que expansión sin pérdidas es posible y no invalidarla por sí misma.

Optimización posterior: más de 2:1 sin pérdidas, más de 35 dB con más de 10:1 con pérdidas, tres imágenes en menos de 20 s en total, sobrecarga menor de 20 %, selección automática, 100 m LOS y 50 m sin LOS. Son objetivos opcionales; no criterios para declarar terminada la primera etapa.
