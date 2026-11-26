# Integración de algoritmos, interfaz y nRF24

**Estado al 26 de noviembre:** imágenes integradas, corte global retirado y
reporte satisfactorio de ambos modos a unos 25 m. Para el uso actual consultar
[operación](../documentacion/operacion.md), para mantener el código el
[mapa de módulos](../documentacion/arquitectura_software.md) y para completar
el montaje la [guía breve de controles](../documentacion/hardware/guia_led_botones.md).
Las rondas de prueba posteriores en este documento conservan sus condiciones históricas.

La web y el proceso de enlace son independientes. Ambos usan el almacenamiento
local `~/.local/share/proyectocomu-web`. Flask nunca abre SPI. `integracion.enlace`
es el único dueño del radio y recibe solicitudes por archivos locales atómicos,
compartidos también con el botón físico. No hay HTTP, sockets ni archivos
compartidos entre Raspberry: el archivo y los metadatos cruzan exclusivamente nRF24.

## Algoritmos del equipo

- `transmision/algoritmos/algoritmo_sin_perdidas`: se conserva el árbol Huffman,
  su desempate y el decodificador del equipo. El adaptador `transmision/codecs.py`
  introduce el contenedor versionado **HUF2**, con longitud original y contador
  de símbolos de 16 bits. Codifica el archivo completo: BMP/PGM con encabezados,
  paleta, orientación y píxeles se recuperan byte por byte. Esto permite todos
  los tamaños que admite la web, incluidos los 256 símbolos posibles, sin
  asumir que una cabecera PGM mide 15 bytes. Las funciones antiguas se conservan
  como referencia; la CLI del compresor ahora produce HUF2 y el descompresor lo reconoce.
- `transmision/algoritmos/con_perdidas`: se utilizan directamente el codificador
  QPG1, el decodificador y el cálculo MSE del equipo. Profundidades de 1 a 7 bits;
  reconstrucción por punto medio y salida PGM. La decodificación en radio es
  **estricta**: no se rellenan archivos incompletos con píxeles inventados.
- Automático: compara Huffman y las siete profundidades de cuantización; elige
  el archivo menor entre los que preservan al menos 25 dB de PSNR o son exactos.
  El tiempo de selección automática se incluye en el tiempo total medido de TX.

La entrada continúa limitada a BMP/PGM gris de hasta 320×240 y 2 MiB. No se
reescala ni se convierte una foto en color de forma silenciosa.

## Web

TX permite cargar/seleccionar imagen, guardar algoritmo y calidad y:

1. **Probar compresión en TX**: comprime y reconstruye localmente, muestra
   métricas medidas, vista previa y descarga del binario. No transmite nada.
2. **Iniciar transmisión por nRF24**: coloca una solicitud para el proceso de
   radio. El botón queda deshabilitado si ese proceso no está activo.

RX muestra el estado real del proceso de enlace, la última imagen guardada y
sus métricas. La última recepción sigue visible aunque se detenga el radio.
El estado del servidor HTTP no se confunde con el estado del proceso nRF24.

La galería de RX conserva las imágenes recibidas y permite abrir cada una con
sus propias métricas o borrarla individualmente, previa confirmación. El borrado
elimina también su registro del historial; si se borra la última imagen, se muestra
la siguiente que siga guardada. Las imágenes antiguas sin registro aparecen sin
métricas inventadas. La galería y el historial sobreviven al reinicio del servidor.

TX permite borrar la imagen seleccionada. Si era la selección guardada, se
retira también esa selección y, cuando corresponde, su compresión local derivada.
El borrado se bloquea mientras haya una transmisión pendiente/en curso o una
compresión local activa. No borra imágenes de la otra Raspberry.

Las rutas son `GET /api/recibidas`, `DELETE /api/recibidas/<nombre>` en RX y
`DELETE /api/imagenes/<nombre>` en TX. Los borrados usan el token de la página.
El estado y la galería se consultan cada tres segundos. Las métricas tienen
etiquetas legibles y conservan el detalle completo desplegable.

MSE/PSNR se calculan en TX comparando original y reconstrucción local. RX recibe
esas medidas identificadas como tales y verifica SHA-256 del archivo reconstruido.
En modo sin pérdidas verifica además el hash del original. No se presenta BER
físico: los paquetes descartados por CRC no llegan al programa. El número de
bytes de tramas de aplicación no incluye todo el tráfico físico de auto-ACK.

## Transporte

Tramas fijas de 32 bytes: cabecera `>BBIH` de 8 bytes (versión/tipo/sesión/índice)
y 24 bytes de datos. Se usan START, DATA, FIN y ACK de aplicación. Se reconoce
cada fragmento, se reintenta si falta respuesta y se deduplican repeticiones.
START repetido de la misma sesión no borra el progreso. FIN repetido devuelve
el cierre almacenado sin reconstruir otra vez. Se verifica longitud y CRC-32 de
todo el flujo, y después los hashes de reconstrucción. Un ACK hardware no
representa éxito de imagen: RX confirma FIN después de reconstruir y guardar.

El límite del flujo es 256 KiB. Esta versión no impone un plazo global de
60 s: una transferencia que sigue avanzando puede terminar después. El tiempo
total se sigue midiendo. Cada trama conserva hasta cuatro repeticiones y una
espera de confirmación de 0,4 s (3 s para el cierre). Los llamadores de
`send_file` pueden solicitar explícitamente un `deadline`, pero el servicio
de imágenes no lo establece. RX descarta una sesión
incompleta tras 10 s de inactividad y guarda los cierres 90 s. Un reinicio puede
interrumpir la transferencia y producir un error explícito; no se promete
reanudar automáticamente una transferencia después de reiniciar el proceso.

La decodificación Huffman resuelve los códigos de hasta 8 bits mediante una
tabla de 256 entradas y recorre el árbol para los códigos más largos. Conserva
HUF2 y los formatos anteriores, la longitud exacta y la validación del relleno.
RX cuenta incrementalmente los bytes únicos recibidos, sin volver a sumar
todos los fragmentos tras cada paquete. Las pruebas de regresión incluyen una
transferencia de más de 60 s de reloj virtual, códigos de 255 bits y ACK perdidos.
Los tiempos de las rondas históricas siguientes corresponden a la versión anterior.

La [revisión posterior a las pruebas de campo](../documentacion/pruebas/2026-11-26-sin-limite/README.md)
documenta la retirada del corte global, las medidas de preparación antes/después
y la diferencia entre una recepción confirmada y un ensayo con reloj virtual.

El resultado de TX conserva también los intentos fallidos en `resultados/<trabajo>.json`.
Su campo `diagnostico` cuenta ACK hardware recibidos/ausentes, ACK de aplicación,
intentos sin respuesta, fragmentos confirmados y tiempo medido en escritura y
espera de confirmaciones. El fallo incluye `confirmado_por_rx: false`; los ACK
hardware no se interpretan como confirmación de imagen. Esta instrumentación no
cambia las tramas ni las esperas del protocolo. Se registra un resumen del fallo
en el journal del servicio de enlace.

`transmision/enlace_imagenes.json` conserva la configuración comprobada de
`~/prueba_radio.py` de **ambas** Raspberry: CE22, CSN0, SPI 1 MHz, canal 76,
250 kbit/s, dirección COMU1, potencia MIN, cargas de 32 bytes y auto-ACK.
No confundir con `transmision/config.json`, que corresponde a la prueba mínima
antigua y usa otros parámetros. No se modifica la prueba de texto original.

## Dependencias y procesos

El entorno web incorpora NumPy. En estas placas los wheels de piwheels requieren
la biblioteca del sistema instalada con `sudo apt install libopenblas0-pthread`.
El proceso de enlace usa `comu-web-venv` y añade a su ruta de importación el
directorio de paquetes del entorno `comu-venv` que ya contiene pyRF24, con el
mismo Python 3.13. No modifica ni reinstala ese entorno de radio.

Desde la raíz del proyecto, comprobar sin abrir SPI/GPIO:

```bash
~/comu-web-venv/bin/python -m integracion.enlace --role tx --check
# En RX, usar --role rx.
```

Inicio manual para pruebas, primero RX y después TX:

```bash
~/comu-web-venv/bin/python -m integracion.enlace --role rx
~/comu-web-venv/bin/python -m integracion.enlace --role tx
```

Cada comando va en su Raspberry. No ejecutar simultáneamente `prueba_radio.py`,
las pruebas mínimas ni dos procesos de enlace sobre el mismo radio. El enlace
usa un bloqueo y rechaza iniciar cuando detecta la prueba anterior en ejecución.

## Controles físicos

La [guía de LED, botón y DIP](../documentacion/hardware/guia_led_botones.md)
incluye pines físicos, tablas y prueba de banco. Describe las limitaciones
actuales: rojo comparte fin/error y azul RX no recibe todavía el modo en su
estado de GPIO. No se consideran validados por los ensayos de imágenes.

`--gpio` habilita LED verde BCM23 (actividad), azul BCM24 (modo con pérdidas),
rojo BCM25 (fin/error), botón BCM17 y DIP BCM27/5/6/13 en TX. El botón usa la
imagen guardada y la configuración DIP: interruptor 1 selecciona modo, 2–3
seleccionan 2/4/6/7 bits y 4 habilita selección automática a 25 dB. Las órdenes
web usan los valores de la página. Ambos caminos comparten la cola, por lo que
no pueden iniciar dos transmisiones a la vez. No se debe ejecutar `hw_test.py`
cuando esos pines estén asignados al enlace.

La instalación inicial deja GPIO sin abrir hasta confirmar el montaje físico;
esta validación no se sustituye con los tests de software. Para probarlo se
detiene el servicio y se inicia el mismo comando manual añadiendo `--gpio`.

## Instalación del paquete ya probado

`integracion/instalar_imagenes.sh` requiere el archivo `~/comu-integracion.tgz`
preparado desde el repositorio y extraído también en `~/ProyectoComu-integracion`.
Valida dependencias, hace una copia del proyecto anterior, instala el código
y `comu-enlace@.service`, reinicia Flask y comprueba su enlace local.
Durante el arranque puede mostrar `Esperando a Flask...` o
`Esperando al proceso de enlace...`; reintenta hasta que ambos estén disponibles.
Si falla durante el cambio, restaura el código anterior y el servidor web.
No cambia redes, AP, la prueba de texto ni los originales de imágenes.

```bash
# En TX:
sudo bash ~/ProyectoComu-integracion/integracion/instalar_imagenes.sh tx
# En RX:
sudo bash ~/ProyectoComu-integracion/integracion/instalar_imagenes.sh rx
```

Los servicios son `comu-web@lobo` / `comu-enlace@lobo` y sus equivalentes `lobor`.
Para volver a ejecutar una prueba de radio antigua, detener primero el servicio
`comu-enlace` correspondiente. La Wi-Fi sigue en PISO 3; activar los AP definitivos
es un paso separado que solo se ejecutará cuando el equipo lo solicite.

## Validación efectuada

**Ronda de tres imágenes aportadas el 26 de noviembre:** las seis transmisiones
reales (tres imágenes en ambos modos) completaron en PISO 3. Sin pérdidas se
verificó identidad con los originales; a 4 bits se midieron PSNR de 33,09–34,91 dB.
Todos los tiempos TX quedaron bajo 60 s, sin reintentos de aplicación.
El [informe completo](../documentacion/pruebas/2026-11-26-tres-imagenes/README.md)
conserva las entradas exactas, los registros de TX/RX, hashes y seis vistas recibidas.

Los tests de códecs utilizan las imágenes reales aportadas por el equipo,
incluidos BMP y PGM, símbolos constantes y los 256 valores posibles. El canal
artificial está definido solo en tests y provoca pérdidas de ACK, corrupción,
duplicación y ausencia de receptor. No existe un modo simulado en producción.

En las Raspberry reales, en PISO 3 y conservando los radios del equipo, se
comprobó por nRF24 una BMP de 64×48 y la imagen `01_fotografica.bmp` de 320×240:

| Prueba real 320×240 | Codificado | Tiempo total TX | Resultado |
|---|---:|---:|---|
| Huffman | 63 469 bytes | 40,67 s | RX confirmó; SHA-256 idéntico al original |
| Cuantización, 4 bits | 38 409 bytes | 20,59 s | RX confirmó; SHA-256 de reconstrucción correcto |

Para la segunda se midió en TX MSE 16,1386 y PSNR 36,0521 dB. No se midió
distancia ni autonomía: no es la prueba de separación considerable o power banks.

Después de instalar los servicios, se inició desde la API HTTP de TX la imagen
que ya estaba cargada, `50830.bmp` (320×240, 77 878 bytes). RX confirmó ambas:
Huffman produjo 63 345 bytes en 40,06 s, con SHA-256 idéntico al original;
cuantización a 4 bits produjo 38 409 bytes en 21,08 s, MSE 23,7227 y
PSNR 34,3792 dB. Se comprobó también la vista PNG servida por RX.
Se restauró la selección previa de TX después del ensayo.

La verificación con teléfonos sobre las páginas actualizadas y los GPIO queda
para la siguiente prueba del equipo.

### Ensayo posterior de diagnóstico: 80–90 cm

El 26 de noviembre se repitió una sola transmisión de
`prueba_proyectocomu_320x240.bmp`, con cuantización a 1 bit, ambos equipos en
PISO 3 y alimentados desde la misma laptop. Se mantuvieron canal, potencia y
protocolo. Separar los radios 80–90 cm no mejoró el resultado: TX avanzó al
32,0 % y terminó por plazo agotado a los 60,06 s. RX alcanzó el 32,2 % y después
declaró recepción incompleta. La compresión tardó 25,06 ms y toda la preparación
78,21 ms; el archivo codificado ocupó 9 609 bytes.

Un observador independiente en RX recogió 198 muestras de `get_throttled` en
unos 100 s, sin indicadores activos de baja tensión ni de limitación de
rendimiento. Permaneció el registro histórico `0x50000`. Esto no comprueba la
estabilidad eléctrica del módulo nRF24 ni descarta caídas demasiado breves para
el muestreo. No se atribuyó la causa a interferencia, alimentación o algoritmo.

Los registros están en `~/comu-diagnosticos/comu-distancia-1795692848892-tx.json`
y su equivalente `-rx.json` en cada Raspberry.

La instrumentación posterior registró 275 escrituras con ACK hardware, 137
confirmaciones de aplicación y 56,89 s esperando respuestas. Ampliar el margen
de respuesta de RX de 3 a 10 ms no resolvió el fallo y se restauró a 3 ms.
Un recorte real de 32×24 sí completó su recepción, pero necesitó 31 reintentos
para 31 confirmaciones. Las cabeceras mostraron ACK de un fragmento anterior:
por ejemplo, al esperar DATA 1 se recibió ACK de DATA 0. Esto localiza el
desfase en el transporte y no en el tiempo de codificación de la imagen.

La corrección limpia TX FIFO y las señales de interrupción antes de
cada escritura bloqueante, y limpia ambas FIFO al inicializar. No se usan
escrituras simultáneas ni cargas de ACK hardware, por lo que no hay una cola
de envíos de aplicación pendiente que deba conservarse entre esas escrituras.
La prueba de regresión modela una trama antigua y una señal TX_DS pendiente;
no sustituye el ensayo con hardware real.

Tras cargar la corrección en ambos procesos se repitió la **imagen completa de
320×240**, conservando la alimentación desde la laptop, separación de 80–90 cm,
PISO 3 y los parámetros de radio. Los compresores no se modificaron durante el
diagnóstico. Ambas transferencias terminaron y fueron confirmadas por RX:

| Modo | Tiempo total TX | Reintentos de aplicación | Verificación |
|---|---:|---:|---|
| Con pérdidas, 4 bits | 22,10 s | 0 | 34,3792 dB; SHA-256 de reconstrucción verificado |
| Sin pérdidas | 42,09 s | 0 | SHA-256 idéntico al archivo original |

Se recibieron 1 628 y 2 666 ACK de aplicación, respectivamente, sin respuestas
fuera de secuencia. El límite de 60 s se conservó. Se verificó la vista PNG
servida por RX a 320×240 y se dejó la selección de TX en con pérdidas, 4 bits.
La imagen de 32×24 era únicamente el recorte del ensayo de cabeceras; los
envíos normales no reducen la resolución del original.

Los resultados están en `~/comu-diagnosticos/ultimo-cola-corregida-4bits.json`
y `ultimo-cola-corregida-sin-perdidas.json` en TX. RX conserva la imagen y sus
métricas en el historial. Estas pruebas no validan aún alcance ni autonomía.

```bash
~/comu-web-venv/bin/python -m unittest transmision.test_imagenes integracion.web.test_web -v
```

Referencia del driver: [API pyRF24](https://pyrf24.readthedocs.io/en/latest/rf24_api.html).
