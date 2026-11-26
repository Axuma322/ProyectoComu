# Hardware disponible en el laboratorio

**Actualización del 25 de noviembre:** el equipo confirmó TX Zero W (`comu-tx`, usuario `lobo`) y RX Pi 4 B (`comu-rx`, usuario `lobor`), detección nRF24L01+ y recepción real de `HOLA COMU` con ACK usando su prueba remota. Ambas tienen `~/comu-venv`. Se conserva abajo el registro anterior; el problema de la segunda Zero W ya no describe la plataforma RX actual. Los Android mostrarán las interfaces locales, conservando botones, interruptores y LED. El AP independiente de cada Pi aún no se activa.

El equipo confirmó que los componentes de las fotografías existen en el Laboratorio de Telecomunicaciones de la UCR. Todavía no hemos contado las unidades, verificado sus modelos ni probado su funcionamiento.

Las fotografías se revisaron el 16 de octubre de 2026, pero fueron retiradas del repositorio. Conservamos aquí las observaciones de esa revisión; no hicimos una nueva identificación visual. Las referencias abreviadas corresponden a archivos llamados `WhatsApp Image 2026-10-14 at [hora].jpeg`.

## Componentes y posibles usos

| Componente / evidencia anterior | Uso en el proyecto | Qué debemos verificar |
|---|---|---|
| Pi de familia Zero: `816aece2-ab13-439e-96a5-e3cad8959702.jpg` | Procesamiento y control en TX/RX; prioridad inicial | Modelo, revisión, GPIO, arranque, OS, SPI y unidades disponibles |
| Placa RF con conector coaxial: `5.44.28 PM (1)` | Candidata nRF24 para el enlace entre dispositivos | Chip y módulo exactos, variante «+», PA/LNA, pinout, alimentación y funcionamiento |
| Antena articulada: `5.44.28 PM` | Transmisión/recepción si es compatible | Frecuencia, ganancia, impedancia y tipo de conector, incluido contacto central |
| Convertidor con USB-A, inductor y terminales +/−: `5.44.29 PM` | Posible alimentación de la Pi desde batería | Entrada/salida, corriente, rizado, polaridad y protecciones; no asumir que carga baterías o sirve para el radio |
| Interfaz microSD con señales SPI: `5.44.30 PM` | Alternativa de almacenamiento | Modelo, niveles eléctricos y lectura/escritura; preferimos la ranura integrada de Pi para empezar |
| Cables USB/OTG y adaptadores de vídeo: `5.44.31 PM` y `(1)` | Alimentación, preparación y conexión de pantalla | Conectores reales, datos frente a solo carga, continuidad, caída de tensión y compatibilidad de vídeo |
| Placa con jack y señales de audio: `5.44.29 PM (1)` | Sin uso necesario en esta etapa | Referencia y función si más adelante se necesita; `(2)` era una copia exacta de la foto, no evidencia de otra unidad |
| Placa circular con símbolo de micrófono: `5.44.30 PM (1)` | Fuera del enlace de imágenes | Identificación provisional; no se asigna función al diseño |
| Puentes y material de prototipado en los fondos | Montaje de conexiones y controles | Separar, contar y comprobar estado; no se identificaron piezas individuales |
| Cables, fuentes y equipos audiovisuales del gabinete: `5.44.32 PM` | Posible apoyo para pruebas | Etiquetas, salidas y compatibilidad; no se confirmó pantalla ni batería adecuada |

Una ranura no confirma que haya una tarjeta instalada. Tampoco podemos deducir cantidades por el número de fotos ni confirmar PA/LNA por el conector de antena.

## Qué falta para montar ambos extremos

La idea es aprovechar las Pi, radios, antenas y cables existentes. Necesitamos comprobar que hay conjuntos compatibles y funcionales para transmisor y receptor antes de buscar reemplazos. La [conexión propuesta](README.md) depende de esa identificación.

Aún debemos localizar almacenamiento, energía autónoma para ambos dispositivos, pantalla para RX, botones, LED, resistencias y desacoplamiento. Son necesidades del montaje, no una lista de compras: primero revisaremos existencias y préstamos. El receptor debe alimentar también su pantalla, salvo que el profesor apruebe otra condición de demostración.

El lector microSD externo y los módulos de audio no hacen falta para empezar. CC1101 y óptica siguen como alternativas investigadas, sin adquisición prevista.

Durante la visita registraremos por unidad: identificación, cantidad, disponibilidad, fotos legibles, tensión/pinout y resultado de prueba con fecha y responsable. Así distinguiremos material existente, identificado, probado y reservado. Primero comprobaremos alimentación y arranque; después SPI y enlace.

Las características generales de las familias están en las [fuentes técnicas](../investigacion/fuentes.md). No se pueden atribuir al módulo concreto hasta identificarlo.

## Lo que se confirmó al montar (24 de noviembre)

- Los radios son módulos **NRF24L01+PA+LNA Ver 3.1** (viene impreso en la placa). El controlador de pyRF24 identifica el chip como nRF24L01+, así que 250 kbit/s sí está disponible.
- Los dos módulos ya tienen antena montada con un adaptador SMA en ángulo. Falta confirmar en una prueba de enlace que el contacto central esté bien.
- Una de las dos Pi arranca con normalidad pero nunca se conecta al Wi-Fi. Al cambiarle la tarjeta a la otra Pi, la tarjeta funcionó, así que el problema es de la placa. Hay que revisar si es una Zero sin W o si está dañada, y pedir otra Zero W en el laboratorio. Para el enlace no hace falta Wi-Fi, pero sin él no se puede programar por SSH.
- Las tarjetas anteriores no estaban disponibles, así que se prepararon dos microSD nuevas: `dinamita` (8 GB, transmisor) y `lobo` (64 GB, receptor). Los detalles de instalación están en [transmisión](../../transmision/README.md).
