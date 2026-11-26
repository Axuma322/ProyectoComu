# Pruebas reales de tres imágenes — 26 de noviembre de 2026

**Resultado: seis de seis transmisiones aprobadas**, con recepción y vista HTTP verificadas en RX. Cada imagen se probó sin pérdidas y con pérdidas a 4 bits. No se modificaron algoritmos, parámetros RF ni redes durante la ronda.

## Montaje y alcance de la prueba

- TX: Raspberry Pi Zero W Rev 1.1, usuario `lobo`; RX: Pi 4 Model B Rev 1.4, usuario `lobor`.
- Ambas permanecieron en `PISO 3`, con Flask y el enlace nRF24 como servicios.
- Configuración de radio: canal 76, 250 kbit/s, COMU1, CE22, CSN0 y SPI de 1 MHz. La versión del enlace utiliza potencia MIN.
- Se mantuvo el montaje del ensayo anterior: separación comunicada de 80–90 cm y alimentación USB desde una laptop. No se midieron distancia ni consumo eléctrico con instrumentos.
- Las imágenes se cargaron en TX mediante su API local. Las imágenes y sus metadatos pasaron de TX a RX exclusivamente por nRF24. SSH solo se usó para conducir y observar el ensayo.
- Identificador: `ensayo-tres-imagenes-1795695943893`. Los archivos originales del ensayo permanecen en `~/comu-diagnosticos/ensayo-tres-imagenes-1795695943893` en cada Raspberry.

Los resultados respaldan la prueba de mesa en estas condiciones. Falta validar la coexistencia con ambos AP activos, el arranque de los procesos actualizados desde alimentación autónoma y el alcance de 30 m.

## Entradas utilizadas

Se usaron exactamente las versiones aportadas desde `D:\descargas`. Las copias de [entradas](entradas/) se verificaron por SHA-256 contra esos archivos y las copias en TX. Se conservan como conjunto separado de las muestras previas del repositorio.

Las tres son BMP grises de 320×240, con 77 878 bytes cada una.

| Archivo | Bytes | SHA-256 original |
|---|---:|---|
| [02_areas_uniformes.bmp](entradas/02_areas_uniformes.bmp) | 77.878 | `d86143bde017996ff46666e0f8ba9bace1942ae28f55eb2a0d84d58c38e072d4` |
| [03_detalle_fino.bmp](entradas/03_detalle_fino.bmp) | 77.878 | `8370cfa4b1b7e5f425bba3b3e2e997a04c2e370b6b6d9c57a2ac6e2849dca00d` |
| [04_patron_geometrico.bmp](entradas/04_patron_geometrico.bmp) | 77.878 | `b6db6f282474aeb2a4245ae7b76f4849cc3d5a5e4701452f5bbfa084a40ec3a9` |

## Resultados

El tiempo de la tabla es `total_tx_ms`: preparación/codificación y envío hasta la confirmación final de RX. No mide el instante en que el navegador del teléfono termina de pintar la imagen.

| Imagen | Modo | Total TX (s) | Bytes codificados | Calidad | Reintentos aplicación | Reintentos hardware | Resultado |
|---|---|---:|---:|---|---:|---:|---|
| 02_areas_uniformes.bmp | Sin pérdidas | 49,12 | 72.902 | Exacta | 0 | 38 | Aprobado |
| 02_areas_uniformes.bmp | Con pérdidas, 4 bits | 21,06 | 38.409 | 34,87 dB | 0 | 16 | Aprobado |
| 03_detalle_fino.bmp | Sin pérdidas | 49,63 | 73.497 | Exacta | 0 | 21 | Aprobado |
| 03_detalle_fino.bmp | Con pérdidas, 4 bits | 21,49 | 38.409 | 34,91 dB | 0 | 27 | Aprobado |
| 04_patron_geometrico.bmp | Sin pérdidas | 43,00 | 61.944 | Exacta | 0 | 40 | Aprobado |
| 04_patron_geometrico.bmp | Con pérdidas, 4 bits | 22,10 | 38.409 | 33,09 dB | 0 | 55 | Aprobado |

Todas completaron antes del límite de 60 s. Los tres archivos sin pérdidas recibidos en RX tienen SHA-256 idéntico al BMP original aportado. En modo con pérdidas, los tres PSNR superan 25 dB y RX verificó el SHA-256 de la reconstrucción prevista por TX.

MSE y PSNR se calcularon en TX comparando el original con la reconstrucción; la igualdad de SHA-256 comprobada sobre el archivo guardado en RX vincula esas métricas con la imagen recibida. No se midió BER físico. Los reintentos hardware de la tabla fueron medidos; **cero reintentos de aplicación no significa ausencia de reintentos del chip**.

El caso más lento fue detalle fino sin pérdidas: 49,63 s. Este margen hasta 60 s debe volver a comprobarse al aumentar distancia o cambiar la alimentación.

## Comprobación independiente en RX

Un observador en RX contrastó cada recepción con su trabajo de TX:

1. Existencia del archivo y dimensiones de 320×240.
2. SHA-256 de reconstrucción y SHA-256 original declarado iguales a los esperados.
3. Identidad byte por byte con el original en modo sin pérdidas.
4. Respuesta HTTP de la vista PNG, dimensiones y píxeles iguales a los del archivo recibido.

Se guardaron las seis vistas obtenidas del servidor de RX en [vistas](vistas/). Ejemplos con pérdidas:

- [02_areas_uniformes.bmp, reconstruida a 4 bits](vistas/02_areas_uniformes-con_perdidas.png).
- [03_detalle_fino.bmp, reconstruida a 4 bits](vistas/03_detalle_fino-con_perdidas.png).
- [04_patron_geometrico.bmp, reconstruida a 4 bits](vistas/04_patron_geometrico-con_perdidas.png).

RX recogió 302 muestras de alimentación, con 0 indicadores activos de baja tensión y 0 de limitación de rendimiento. Persistió la marca histórica `0x50000`; este muestreo no descarta caídas breves ni mide la estabilidad de la línea de 3,3 V del radio.

Las tres entradas quedaron disponibles en TX y las seis recepciones en la galería de RX. Como la selección previa de TX era vacía, quedó seleccionada la última entrada, patrón geométrico, con pérdidas a 4 bits. Ambos AP mantuvieron la autoconexión deshabilitada.

## Evidencia y repetición

- [Resultado combinado](resultados.json): casos unidos por identificador de trabajo, entradas y entorno.
- [Registro de TX](resultados-tx.json) y [validaciones independientes de RX](validaciones-rx.json).
- [Entorno TX](entorno-tx.json) y [entorno RX](entorno-rx.json): placa, kernel, red activa, configuración RF y SHA-256 de cuatro archivos de código.
- [Muestreo de alimentación RX](alimentacion-rx.json).
- [Guion TX](ensayo-tx.py), [guion RX](ensayo-rx.py) y [manifiesto de entradas](entradas.json).

Para repetir, copiar este conjunto a una carpeta nueva en cada Raspberry, con el proyecto y servicios activos. En RX ejecutar primero su guion con la carpeta de ensayo como argumento; después ejecutar el guion TX con el entorno `~/comu-web-venv/bin/python`. El observador RX guarda y valida solo recepciones nuevas. Al terminar TX y comprobar las seis validaciones, crear `detener-observador` en la carpeta de RX. El guion RX termina automáticamente a los diez minutos si no recibe ese marcador. Conservar una carpeta distinta para cada ronda evita sobrescribir evidencia anterior.

No hubo commits ni push automáticos. La activación de los AP y las pruebas con power banks quedan como pasos posteriores.

