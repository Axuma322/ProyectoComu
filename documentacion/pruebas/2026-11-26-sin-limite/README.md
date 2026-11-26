# Transmisiones sin corte global y preparación Huffman

## Motivo

El equipo consiguió transmitir con pérdidas en campo, pero un envío sin pérdidas
terminó cerca del 95 % por el límite global de 60 segundos. El resultado real de
TX `a15186544ee54f5b81d6c33637727761` confirmó 2 730 de 2 844 fragmentos (96,0 %)
antes del corte: 60,001 s totales, 6,415 s de preparación, 29 reintentos de
aplicación y 1 659 reintentos hardware. No había terminado ni se confirmó la
imagen completa.

La imagen era `01_fotografia_retrato.bmp`, 320 × 240, 77 878 bytes,
SHA-256 `03fcdf4871f5375db91bb36ad8730eb8da2e5f77d65ede65d37805d43e1ee067`.
El flujo Huffman ocupaba 67 670 bytes. Estos registros muestran tanto el corte
por tiempo como las retransmisiones; no permiten atribuir todas las pérdidas
a una causa física concreta.

## Cambios

- El servicio deja de pasar un plazo global a `send_file`; esta función tampoco
  crea uno implícitamente. El tiempo se sigue midiendo y mostrando.
- Se conservan la espera de ACK por trama (0,4 s; 3 s para FIN), cuatro
  repeticiones y el descarte de una sesión RX tras 10 s sin fragmentos. Un enlace
  sin respuesta todavía puede fallar; continuar con progreso no depende de
  terminar antes de 60 s.
- Huffman usa una tabla de 256 prefijos de 8 bits para los códigos cortos y el
  árbol para códigos largos. El codificador, HUF2, los bytes comprimidos y la
  reconstrucción se conservan.
- RX suma los bytes de cada fragmento nuevo, evitando recorrer todos los ya
  recibidos. Los duplicados no aumentan el progreso.

No se cambiaron canal, potencia, velocidad, dirección, FIFO, configuración
Wi-Fi, botones, interruptores, LED ni `prueba_radio.py`.

## Medición de CPU en la TX real

Mismo proceso de comparación en la Pi Zero W, con el decodificador que estaba
instalado y el nuevo. Se comprobó que ambos producen el mismo flujo comprimido
y reconstruyen exactamente el original. Son medidas de **preparación**,
incluida la comprobación local; no son tiempos de transmisión por radio.
Una medición por imagen, sin estimación estadística de variabilidad:

| Imagen | Antes | Después | Reducción |
|---|---:|---:|---:|
| `02_areas_uniformes.bmp` | 7,353 s | 3,836 s | 47,8 % |
| `03_detalle_fino.bmp` | 7,169 s | 3,276 s | 54,3 % |
| `04_patron_geometrico.bmp` | 6,166 s | 3,793 s | 38,5 % |
| `01_fotografia_retrato.bmp` | 6,664 s | 3,367 s | 49,5 % |

Estas reducciones no eliminan retransmisiones debidas al enlace. El primer
resultado de campo y este ensayo de CPU son condiciones distintas.

## Validación automatizada y despliegue

Las 27 pruebas de códecs, transporte y web pasaron en **ambas Raspberry**, en
una copia aislada antes del despliegue. Incluyen archivos reales del equipo,
códigos Huffman de hasta 255 bits, relleno inválido, corrupción, pérdida de ACK
y progreso sin duplicados. La transferencia que supera 60 s utiliza **reloj
virtual** en una prueba unitaria: no se presenta como un envío de campo.

Se guardó una copia de los archivos anteriores en cada placa:
`~/comu-diagnosticos/optimizacion-tiempo-1795701100664/codigo-anterior.tgz`.
Se reiniciaron los servicios web y de enlace y se comprobó que ambas seguían en
PISO 3, con la web respondiendo y el radio disponible. Las redes permanecen en
modo de desarrollo durante la verificación de los envíos.

`ensayo_tx.py` inicia desde la API HTTP local un envío sin pérdidas y otro con
pérdidas de la imagen seleccionada; restaura la selección y comprueba que la
fuente no cambió. Su límite de observación de 240 s no cancela la transmisión.
La recepción debe verificarse independientemente en RX por trabajo y SHA-256.

## Envíos reales después de actualizar

El primer intento de organizar el ensayo se interrumpió al perder el acceso
SSH. El equipo informó de que se había apagado la alimentación compartida.
Al volver a encenderlas se comprobaron los servicios iniciados automáticamente,
se recuperó SSH y se completaron estos **dos envíos reales por nRF24** desde la
API HTTP local, con ambos equipos en PISO 3:

| Modo | Bytes codificados | Preparación TX | Total TX | Reintentos aplicación / hardware | Resultado |
|---|---:|---:|---:|---:|---|
| Sin pérdidas | 67 670 | 3,330 s | 41,993 s | 1 / 68 | SHA-256 idéntico al original |
| Con pérdidas, 5 bits | 48 009 | 0,197 s | 26,618 s | 0 / 10 | SHA-256 de reconstrucción correcto; PSNR 41,212 dB |

Ambas imágenes conservan 320 × 240 píxeles. RX comprobó de forma independiente
el archivo guardado, la correspondencia del trabajo y los píxeles de la vista
PNG servida por HTTP. La descompresión y guardado medidos en RX fueron 267,1 ms
sin pérdidas y 28,4 ms con pérdidas. La selección previa de TX se restauró a
con pérdidas, 5 bits, y la fuente quedó sin cambios.

Trabajos: `42a9e0237bed407ca8e2ea5a1f09b5b2` (sin pérdidas) y
`1024bf3dbd0e4baa84665b6b206d6e31` (con pérdidas). Los registros completos son
`resumen-tx.json`, `sin_perdidas-tx.json`, `con_perdidas-tx.json` y
`validaciones-rx.json`. `estado-final-tx.json` y `estado-final-rx.json` conservan
los hashes del código instalado y el estado de systemd: ambos servicios activos,
habilitados y con `RuntimeMaxUSec=infinity`.

Estos envíos terminaron antes de 60 s; la ausencia del corte a los 60 s se
comprueba con la prueba unitaria de reloj virtual y la revisión del código,
**no con un envío físico de más de un minuto en esta ronda**. No se midió
distancia ni autonomía. Los tiempos de campo con muchas retransmisiones no se
comparan directamente con esta ronda en PISO 3.

## Observación de alimentación

TX informó `throttled=0x0` en la consulta final. RX pasó de `0x50000` al comienzo
a `0x50005` en la consulta posterior a los envíos. Un seguimiento posterior de
10 muestras, separadas dos segundos, registró dos con `0x50005` y ocho con
`0x50000`. No fue una observación continua durante la transmisión.

Los bits bajos `0x1` y `0x4` indican baja tensión y limitación activas; los bits
`0x10000` y `0x40000` conservan antecedentes. Véase la
[documentación oficial de get_throttled](https://www.raspberrypi.com/documentation/computers/os.html#get_throttled).
Se debe revisar la alimentación y el cable de RX antes de comparar alcance y
rendimiento. Este registro no demuestra que la tensión causara las pérdidas
de paquetes de campo. Datos: `alimentacion-rx-despues.json`.

## Repetición y reversión

Con las placas accesibles, la fuente seleccionada y los servicios activos, en TX:

```bash
cd ~/ProyectoComu
~/comu-web-venv/bin/python documentacion/pruebas/2026-11-26-sin-limite/ensayo_tx.py \
  --salida ~/comu-diagnosticos/repeticion-sin-limite
```

El script conserva los dos trabajos nuevos en `resumen-tx.json`. Para verificar
esos trabajos en RX, reemplazar `SHA_ORIGINAL`, `TRABAJO_1` y `TRABAJO_2` por los
valores de ese resumen:

```bash
cd ~/ProyectoComu
~/comu-web-venv/bin/python documentacion/pruebas/2026-11-26-sin-limite/verificar_rx.py \
  --salida ~/comu-diagnosticos/repeticion-validaciones-rx.json \
  --sha256-original SHA_ORIGINAL TRABAJO_1 TRABAJO_2
```

Si se necesita revertir el código de esta actualización, en **cada placa**,
sin una transmisión en curso:

```bash
tar -C ~/ProyectoComu -xzf \
  ~/comu-diagnosticos/optimizacion-tiempo-1795701100664/codigo-anterior.tgz
sudo systemctl restart "comu-web@$(id -un).service" "comu-enlace@$(id -un).service"
```

La reversión restaura también el corte anterior de 60 s. No cambia la Wi-Fi.
Las instrucciones para volver a los AP persistentes, cuando se vaya al campo,
siguen en [redes_definitivas.md](../../despliegue/redes_definitivas.md).

`comparacion-huffman.json` conserva las mediciones CPU, `antecedentes-campo.json`
los ocho resultados anteriores consultados en TX y `pruebas-tx.log` /
`pruebas-rx.log` las 27 pruebas automatizadas en cada placa.
