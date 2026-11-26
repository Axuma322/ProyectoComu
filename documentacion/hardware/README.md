# Conexiones de hardware

**Estado al 26 de noviembre:** TX es una Zero W y RX una Pi 4 B. Cada teléfono
abre la web local mediante AP independiente. El equipo reportó imágenes en
ambos modos a unos 25 m. Los controles de las placas actuales se comprueban
con la [guía breve de LED, botón y DIP](guia_led_botones.md). La web no abre
GPIO; los controla el worker únicamente con `--gpio`.

Se aprovechan los componentes del laboratorio antes de proponer compras. El
[inventario](inventario.md) reúne lo observado y las comprobaciones pendientes;
las conexiones siguientes documentan señales y el montaje histórico.

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
| IRQ | Sin conectar: GPIO24 está reservado al LED azul | — |

CE controla el modo del radio; CSN selecciona el dispositivo SPI. El rótulo CE0 de la Pi corresponde a CSN en esta conexión.

No debemos aplicar 5 V a VCC del radio sin regulador ni a los GPIO. Si el módulo tiene PA/LNA, planteamos un regulador dedicado de 3,3 V desde la batería, compartiendo tierra con la Pi. Primero hay que comprobar si el adaptador disponible incluye regulación y qué corriente entrega.

Usaremos cables cortos y desacoplamiento junto al módulo. Como punto de partida estudiaremos 100 nF y 10–47 µF, ajustándolos según la ficha del módulo y la tensión medida durante transmisión y ACK. Estos valores no garantizan estabilidad por sí solos. [Nordic y problemas comunes de RF24](../investigacion/fuentes.md)

## Controles, almacenamiento y alimentación

GPIO17 es inicio TX; GPIO27/5/6/13, DIP TX; GPIO23/24/25, LED de ambos equipos.
La [guía de controles](guia_led_botones.md) da pines físicos, resistencias,
pull-up y antirrebote. RX escucha sin pulsación sincronizada con TX.

La microSD de cada Pi almacena imágenes y registros; no hace falta un lector
externo. La interfaz adoptada se visualiza en el navegador del teléfono.

Falta documentar consumo y autonomía del conjunto, incluida recepción continua.
Las pruebas de software registraron baja tensión intermitente en RX; ver
[informe](../pruebas/2026-11-26-sin-limite/README.md#observación-de-alimentación).
Conservar alimentación estable, medir picos/caída de tensión y comprobar el
autoapagado del banco USB. Prever apagado seguro para la microSD.

## Montaje del transmisor (24 de noviembre)

Se armó la primera versión del transmisor en `dinamita`. GPIO23 pasó a ser uno
de tres LED y GPIO24 se usó para el azul porque IRQ no se conectó. La asignación
completa vigente está en la [guía de controles](guia_led_botones.md).

El radio se conectó con cables hembra-hembra directo al conector del módulo, sin pasar por la protoboard: el conector de 2×4 quedaría en corto por pares si se inserta. Se usó la misma tabla de arriba con dos cambios menores: GND en el pin 20 en vez del 25, solo por comodidad del cableado, y VCC en el pin 1. Hay que tener cuidado porque el pin 1 queda junto a los pines 2 y 4, que son de 5 V.

Por ahora el módulo se alimenta directo del 3,3 V de la Pi y sin condensador de desacople, porque no teníamos. Así funciona en potencia LOW con los radios cerca, pero antes de subir la potencia para la prueba a 30 m hay que poner uno de 10 a 100 µF pegado a VCC y GND del módulo.

Para la autonomía se están usando bancos USB conectados al puerto PWR IN. Falta revisar si se apagan solos con el consumo bajo de la Pi Zero.
