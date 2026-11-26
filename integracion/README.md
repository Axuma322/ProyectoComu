# Integración

Aquí van quedando las piezas que juntan el radio, la codificación y los controles de cada Pi. La [interfaz Flask](web/README.md) es independiente de la prueba de señalización: no abre el radio ni modifica los GPIO. TX es una Zero W y RX una Pi 4 B.

La web permite cargar y seleccionar imágenes y guardar el modo en TX. La transferencia y los códecs siguen pendientes; RX no presenta imágenes ni métricas ficticias. La prueba de radio confirmada por el equipo (`~/prueba_radio.py`) se mantiene separada. La decisión vigente es usar AP abiertos independientes y Flask automático, siguiendo la [migración con recuperación](web/RED_LOCAL.md), primero TX y después RX.

## Prueba de LED, botón y DIP

`hw_test.py` sirve para revisar el montaje de la protoboard antes de conectar el radio. Enciende los tres LED en orden (verde, azul, rojo), muestra en consola el estado del DIP cada vez que cambia y hace parpadear los LED al presionar el botón. No usa el radio ni pyRF24.

Se corre directo con el Python del sistema, porque gpiozero ya viene en Raspberry Pi OS:

```bash
python3 integracion/hw_test.py
```

Se sale con Ctrl+C.

Pines usados (numeración BCM, entre paréntesis el pin físico):

| Elemento | GPIO | Uso |
|---|---|---|
| LED verde | 23 (16) | Actividad, transmitiendo o recibiendo |
| LED azul | 24 (18) | Modo con pérdidas |
| LED rojo | 25 (22) | Fin o error |
| Botón | 17 (11) | Inicio |
| DIP 1 | 27 (13) | Modo con o sin pérdidas |
| DIP 2 y 3 | 5 y 6 (29 y 31) | Nivel de calidad, 2 bits (0 a 3) |
| DIP 4 | 13 (33) | Selección automática del modo |

Los LED llevan resistencia de 220 Ω hacia GND. El botón y los interruptores del DIP van a GND y usan el pull-up interno, así que en ON se leen como presionados. El DIP solo va en el transmisor; en el receptor el script lee todo en OFF y no pasa nada.

Con los interruptores 2 y 3 se eligen los cuatro puntos de operación del modo con pérdidas para la curva tasa-distorsión.

El 24 de noviembre se probó en `dinamita` y funcionó todo: los tres LED, el botón y los cuatro interruptores.
