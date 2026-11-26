# Guía breve: LED, botón y DIP

Para el equipo que montará los controles de **TX Zero W y RX Pi 4 B**.
El código está en `integracion/enlace.py`, clase `Controls`; la prueba de banco
es `integracion/hw_test.py`. El software de radio probado se conserva.

## 1. Cableado

Usamos **numeración BCM** en Python; «pin físico» es la posición del conector de
40 pines. Montar con las fuentes desconectadas y comprobar orientación del cabezal.

| Elemento | BCM | Pin físico | Equipo |
|---|---:|---:|---|
| LED verde: actividad | 23 | 16 | TX y RX |
| LED azul: modo | 24 | 18 | TX y RX; ver limitación RX abajo |
| LED rojo: fin/error | 25 | 22 | TX y RX |
| Botón: enviar (TX) / habilitar recepción (RX) | 17 | 11 | TX y RX |
| DIP 1: modo | 27 | 13 | TX |
| DIP 2: calidad, bit alto | 5 | 29 | TX |
| DIP 3: calidad, bit bajo | 6 | 31 | TX |
| DIP 4: automático | 13 | 33 | TX |
| GND local común | — | 6, por ejemplo | Ambos |

Cada LED: `GPIO → resistencia serie → ánodo LED; cátodo → GND`. El montaje
anterior usó 220 Ω; comprobar la corriente del LED elegido y dimensionar la
resistencia antes del montaje definitivo. No conectar un LED sin resistencia.
Cada pulsador/contacto DIP conecta **su GPIO a GND**, con pull-up interno.
Abierto = OFF; cerrado a GND = ON (`is_pressed=True`). GPIO trabaja a 3,3 V;
no aplicar 5 V. [GPIO oficiales](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#gpio),
[LED](https://gpiozero.readthedocs.io/en/stable/api_output.html#led) y
[Button](https://gpiozero.readthedocs.io/en/stable/api_input.html#button).

Reservados para radio: BCM22/8/11/10/9, pines físicos 15/24/23/19/21.
**IRQ del radio queda sin conectar: BCM24 es el LED azul.** No confundir BCM22
(CE de radio, físico 15) con el pin físico 22 (LED rojo, BCM25).

## 2. Botón, DIP y LED durante la operación

Desde el 26 de noviembre el teléfono **solo elige la imagen**: cargarla o
escogerla en la lista ya la deja lista. El modo y los bits se ponen con el DIP y
la transmisión se inicia únicamente con el botón físico; la web ya no tiene
botón de envío y `/api/transmitir` responde 403. La página muestra en vivo lo
que marcan los switches. Si se pulsa sin imagen elegida, o con un envío en
curso, no se encola nada y el LED rojo da unos destellos. Antirrebote: 0,1 s.
En RX el botón habilita la recepción. Con `--gpio`, RX arranca **en pausa**
(radio sin escuchar, rojo con un destello cada 2 s). Una pulsación lo pone a
escuchar y queda así indefinidamente, sin saber cuándo empezará TX; otra
pulsación vuelve a la pausa. Si llega a pulsarse mientras recibe una imagen,
se ignora y el rojo destella. Sin `--gpio`, RX escucha siempre, como antes.
RX no tiene DIP. En RX el botón puede ir a cualquier GND libre (por ejemplo,
el pin 9).

Por esto **TX necesita `--gpio` siempre activo**; sin él no hay forma de
transmitir. Ver [GPIO persistentes](../operacion.md#gpio-persistentes).

| DIP 4 | DIP 1 | Modo al pulsar |
|---|---|---|
| OFF | OFF | Sin pérdidas |
| OFF | ON | Con pérdidas |
| ON | Cualquiera | Automático, objetivo PSNR ≥ 25 dB o exacto |

| DIP 2 | DIP 3 | Bits en modo con pérdidas |
|---|---|---:|
| OFF | OFF | 2 |
| OFF | ON | 4 |
| ON | OFF | 6 |
| ON | ON | 7 |

El DIP se lee al pulsar; cambiarlo durante una transmisión no cambia el
trabajo en curso. «Probar compresión» en la web usa también los valores DIP.

Los patrones están en `integracion/senales.py` (función `patron`, probada en
`integracion/test_senales.py` sin GPIO). Son iguales en TX y RX salvo el azul:

| Situación | Verde | Azul | Rojo |
|---|---|---|---|
| Arranque del worker | Barrido verde → azul → rojo, una vez | | |
| TX esperando / RX escuchando | Destello corto cada 2 s | Ver abajo | Apagado |
| Codificando (TX) | Parpadeo rápido | | |
| Enviando / recibiendo | Fijo | | |
| Completado y confirmado | 3 destellos, luego vuelve al latido | | Apagado |
| Error de la transferencia | Apagado | | Parpadeo rápido 5 s, luego fijo |
| Error del radio o detenido | Apagado | | Fijo |
| RX en pausa (no recibe) | Apagado | | Destello corto cada 2 s |
| Botón sin imagen o ya ocupado | | | Destellos durante 1 s |

Azul en TX: mientras espera (o después de un envío) sigue al DIP en tiempo real.
Apagado sin pérdidas, encendido con pérdidas, parpadeo lento automático. Durante
el envío muestra el modo que realmente se resolvió. Azul en RX: modo con que
llegó la última imagen (encendido con pérdidas).

## 3. Probar el montaje sin transmitir

En la Raspberry que se va a probar, entrando como `lobo` o `lobor`:

```bash
cd ~/ProyectoComu
sudo systemctl stop "comu-enlace@$(id -un).service"
~/comu-web-venv/bin/python integracion/hw_test.py
```

Debe encender verde/azul/rojo en secuencia, imprimir cambios DIP y hacer
parpadear los tres LED al pulsar. Este script abre también las entradas aunque
se ejecute en RX; su señalización es de banco, distinta de la de producción.
Al terminar con Ctrl+C, restaurar el servicio:

```bash
sudo systemctl start "comu-enlace@$(id -un).service"
```

Si faltan permisos o backend GPIO, conservar el error y comprobar acceso a GPIO
y gpiozero en `comu-web-venv`; no sustituir el servicio por ejecución permanente
como root. No ejecutar esta prueba junto con `integracion.enlace --gpio`.

## 4. Probar con el enlace real

Detener solo el servicio de enlace y ejecutar **un** worker manual:

```bash
cd ~/ProyectoComu
sudo systemctl stop "comu-enlace@$(id -un).service"
~/comu-web-venv/bin/python -m integracion.enlace --role tx --gpio
# En la Raspberry RX usar --role rx --gpio.
```

Mantener la web activa. Comprobar `/api/estado`: `enlace.gpio` debe ser `true`.
Probar botón, cuatro niveles DIP, automático y envío desde web; comprobar que
no haya doble envío. Terminar con Ctrl+C y volver a iniciar el servicio como
en el paso anterior. Para que `--gpio` sobreviva al encendido usar el
[procedimiento systemd reversible](../operacion.md#gpio-persistentes).

Registrar equipo, pines comprobados, estado de cada LED, lectura DIP y resultado
del envío. La prueba de imágenes a 25 m no sustituye esta validación física.
