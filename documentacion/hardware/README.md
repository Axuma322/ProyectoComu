# Conexión de la Pi Zero y el radio

Usaremos los componentes del laboratorio antes de proponer compras. El [inventario](inventario.md) reúne lo observado y las comprobaciones pendientes; aquí dejamos la conexión inicial.

## SPI y señales de control

Este pinout sigue el ejemplo de [RF24 para Raspberry Pi](https://nrf24.github.io/RF24/md_docs_2rpi__general.html). Debemos comprobar orientación y referencia del módulo antes de cablear. Los números BCM identifican GPIO; los números físicos indican posiciones del conector.

| Señal del radio | Pi: función / BCM | Pin físico |
|---|---|---|
| GND | Tierra común | 25 |
| VCC | 3,3 V regulados | 17, solo si permite alimentar el módulo elegido |
| CE | GPIO22 | 15 |
| CSN | GPIO8 / SPI0 CE0 | 24 |
| SCK | GPIO11 | 23 |
| MOSI | GPIO10 | 19 |
| MISO | GPIO9 | 21 |
| IRQ, opcional | GPIO24 | 18 |

CE controla el modo del radio; CSN selecciona el dispositivo SPI. El rótulo CE0 de la Pi corresponde a CSN en esta conexión.

No debemos aplicar 5 V a VCC del radio sin regulador ni a los GPIO. Si el módulo tiene PA/LNA, planteamos un regulador dedicado de 3,3 V desde la batería, compartiendo tierra con la Pi. Primero hay que comprobar si el adaptador disponible incluye regulación y qué corriente entrega.

Usaremos cables cortos y desacoplamiento junto al módulo. Como punto de partida estudiaremos 100 nF y 10–47 µF, ajustándolos según la ficha del módulo y la tensión medida durante transmisión y ACK. Estos valores no garantizan estabilidad por sí solos. [Nordic y problemas comunes de RF24](../investigacion/fuentes.md)

## Controles, almacenamiento y alimentación

Podemos reservar GPIO17 para inicio, GPIO27 para seleccionar modo en TX y GPIO23 para el LED, si la pantalla no utiliza esas señales. El botón necesita polarización y antirrebote; el LED, resistencia adecuada. El receptor se arma una vez y permanece escuchando, sin pulsación sincronizada con el transmisor.

La microSD de la Pi puede almacenar imágenes y registros; no necesitamos añadir un lector externo para empezar. La pantalla será un periférico de la misma Pi, sin incorporar otro módulo programable.

Todavía debemos seleccionar batería y pantalla. Mediremos el consumo completo, incluida la recepción continua y el despliegue. Para estimar autonomía usaremos energía de batería en Wh × eficiencia / potencia media en W, y comprobaremos picos, caída de tensión y posible autoapagado del banco USB. También debemos prever apagado seguro para no corromper la microSD.
