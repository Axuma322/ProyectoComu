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
| Botón de inicio | 17 | 11 | TX |
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

Primero cargar y guardar una imagen desde la web. Al pulsar, TX toma esa imagen
y lee el DIP; los valores DIP sustituyen modo/bits para ese trabajo sin cambiar
la selección guardada. Sin selección no se encola nada. Si ya hay un envío,
la pulsación adicional no inicia otro. Antirrebote de producción: 0,1 s.
RX escucha automáticamente; su worker no crea botón ni entradas DIP.

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

La web usa sus propios valores (1–7 bits); el DIP se consulta solo al pulsar.
Cambiarlo durante una transmisión no cambia el trabajo en curso.

| LED | Comportamiento de producción con `--gpio` |
|---|---|
| Verde | Encendido en `codificando`, `enviando` o `recibiendo` |
| Azul | En TX refleja el último modo resuelto publicado: encendido con pérdidas; apagado sin pérdidas |
| Rojo | Encendido en `completado` o `error`; no distingue éxito de fallo |

No son patrones de parpadeo de progreso. El rojo se apaga al salir de esos
estados; no cubre todos los fallos de inicialización. El azul no sigue el DIP
en tiempo real. **En RX todavía falta propagar el modo recibido al estado que
consume `Controls.show`; hoy su LED azul permanece apagado.** Esa adaptación
y la prueba de los LED de RX son pendientes de integración, no de cableado.

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
