# Hardware: inventario, conexión y decisiones

Fuentes: [consigna C, Nordic N, Raspberry Pi P, RF24 RL/RI/RP](../investigacion/fuentes.md); evidencia visual en [recursos](../../recursos/). «Visible» significa reconocido en fotografía, no inspeccionado físicamente ni probado. Cantidades de la tabla son necesidades del diseño; existencias por contar.

## Inventario y prioridad de aprovechamiento

El equipo confirmó que los componentes fotografiados existen físicamente en el Laboratorio de Telecomunicaciones de la UCR. El [inventario visual](inventario.md) concentra evidencia por fotografía, posibles funciones, verificaciones pendientes, utilidad TX/RX y necesidades adicionales por comprobar. Las cantidades, variantes, disponibilidad para préstamo y funcionamiento siguen sin verificar.

La solución inicial prioriza las Raspberry Pi Zero, radios, antenas, alimentación y cables del laboratorio. Revisar existencias y opciones de préstamo antes de proponer compras. Los módulos de audio y el lector microSD externo no son indispensables; la pantalla y la energía autónoma requieren selección tras revisar el material disponible.

## Conexión preliminar por extremo

Propuesta conforme al pinout RF24 para GPIO de 40 posiciones; **validar placa, orientación y módulo antes de cablear**. BCM y número físico no son intercambiables.

| Señal radio | Pi BCM / función | Pin físico |
|---|---|---|
| GND | Tierra común | 25 |
| VCC | 3,3 V regulados | 17 solo si el presupuesto eléctrico del módulo lo permite |
| CE radio | GPIO22 | 15 |
| CSN radio | GPIO8, SPI0 CE0 | 24 |
| SCK | GPIO11 | 23 |
| MOSI | GPIO10 | 19 |
| MISO | GPIO9 | 21 |
| IRQ opcional | GPIO24 | 18 |

CE de radio controla modo y no es CSN; el rótulo CE0 de Pi corresponde aquí a selección SPI. Para PA/LNA se propone regulador dedicado de 3,3 V desde la batería del dispositivo, con tierra común; no una fuente de pared durante la demostración. No aplicar 5 V a VCC del radio desnudo ni a GPIO de Pi. No asumir que una placa adaptadora incluye regulación.

Desacoplar cerca del módulo: condensador cerámico y reserva local dimensionados con ficha y medición de rizado; como hipótesis de montaje, estudiar 100 nF más 10–47 µF, sin presentarlos como garantía universal. Usar cables cortos, buena tierra y fuente con capacidad para transitorios; observar tensión durante TX y ACK con osciloscopio. Los valores propuestos son de diseño, pendientes de validar. Las advertencias RF24 sobre PA/LNA justifican separar la regulación del radio.

Botón de inicio: entrada GPIO con polarización y contacto a tierra, antirrebote; LED mediante resistencia calculada según tensión directa/corriente seleccionada. Reserva sugerida: GPIO17 inicio, GPIO27 selector en TX y GPIO23 LED; comprobar conflictos con pantalla antes de fijar. Receptor: botón arma/enciende servicio y después mantiene RX; no necesita pulsación sincronizada con TX. Patrones luminosos deben distinguir espera, TX/RX, final y fallo; TX indica además modo seleccionado.

## Procesamiento, visualización y energía

Cada Pi ejecuta lectura, interfaz humana, transferencia y futura codificación. El nRF24 es periférico de radio, no un segundo módulo programable. Preferir pantalla HDMI como periférico o panel SPI con controlador fijo; una segunda Pi/Arduino para mostrar datos rompería la arquitectura prevista. La pantalla debe alimentarse dentro del presupuesto autónomo del receptor. Preguntar al docente si un monitor de laboratorio alimentado externamente sería admisible; no asumirlo.

No se usa cámara: C pide archivo almacenado. Inicialmente almacenar en microSD local, permitido por especificación 8; USB extraíble queda como alternativa con adaptador OTG. Guardar archivo recibido y logs con escritura atómica; evitar corrupción al apagar la Pi y definir apagado seguro.

Autonomía estimada = energía útil de batería en Wh × eficiencia / potencia media del conjunto en W. Medir con radio en RX permanente y pantalla encendida; incluir picos y autoapagado de bancos USB. No asignar horas de autonomía sin datos. El presupuesto monetario se completa con cantidades físicas y cotizaciones: hoy todos los costos son pendientes, no cero.
