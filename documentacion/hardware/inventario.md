# Inventario visual del hardware del laboratorio

Fecha: 16 de octubre de 2026. Base: fotografías originales en [`recursos/`](../../recursos/) y confirmación del equipo de que los componentes fotografiados existen físicamente en el Laboratorio de Telecomunicaciones de la UCR. Esa existencia se considera confirmada por el equipo; no equivale a inspección presencial, disponibilidad para préstamo, cantidad suficiente ni funcionamiento verificado.

La solución inicial debe aprovechar prioritariamente las Raspberry Pi Zero y los módulos de radio existentes. Las identificaciones visuales de familia o función son provisionales cuando no se lee una referencia. No se deducen cantidades a partir del número de fotos: pueden mostrar repetidamente el mismo componente. Todas las existencias y pruebas funcionales quedan pendientes de registro.

## Evidencia fotográfica

| ID | Fotografía original | Observación |
|---|---|---|
| F01 | [Placa de formato Zero](../../recursos/816aece2-ab13-439e-96a5-e3cad8959702.jpg) | Placa, ranura microSD, conectores micro-USB, vídeo y cabecera GPIO |
| F02 | [Antena](../../recursos/WhatsApp%20Image%202026-10-14%20at%205.44.28%20PM.jpeg) | Antena articulada y conector roscado; banda/ganancia no legibles |
| F03 | [Módulo de radio](../../recursos/WhatsApp%20Image%202026-10-14%20at%205.44.28%20PM%20%281%29.jpeg) | Placa RF con conector coaxial y componentes adicionales; referencia no legible |
| F04 | [Módulo con USB](../../recursos/WhatsApp%20Image%202026-10-14%20at%205.44.29%20PM.jpeg) | Puerto USB-A, inductor, condensador y terminales marcados +/− |
| F05 | [Placa de audio](../../recursos/WhatsApp%20Image%202026-10-14%20at%205.44.29%20PM%20%281%29.jpeg) | Jack y señales SCK/BCK/DIN/LCK; función exacta por identificar |
| F06 | [Copia de F05](../../recursos/WhatsApp%20Image%202026-10-14%20at%205.44.29%20PM%20%282%29.jpeg) | Duplicado exacto por SHA-256; no acredita una unidad adicional |
| F07 | [Lector microSD](../../recursos/WhatsApp%20Image%202026-10-14%20at%205.44.30%20PM.jpeg) | Ranura y señales CS/SCK/MOSI/MISO/VCC/GND visibles |
| F08 | [Placa circular de audio](../../recursos/WhatsApp%20Image%202026-10-14%20at%205.44.30%20PM%20%281%29.jpeg) | Símbolo de micrófono y señales SCK/WS/SD; identificación provisional |
| F09 | [Cables y adaptadores](../../recursos/WhatsApp%20Image%202026-10-14%20at%205.44.31%20PM.jpeg) | Cables USB y adaptadores de vídeo; empaque rotulado micro-USB OTG |
| F10 | [Detalle de adaptadores](../../recursos/WhatsApp%20Image%202026-10-14%20at%205.44.31%20PM%20%281%29.jpeg) | Conectores de vídeo y empaque OTG; verificar cada pieza |
| F11 | [Gabinete de equipos](../../recursos/WhatsApp%20Image%202026-10-14%20at%205.44.32%20PM.jpeg) | Altavoces aparentes, cables, adaptadores de alimentación y equipo audiovisual |

## Componentes observados y aprovechamiento

En todas las filas, la cantidad total, el estado operativo y la asignación al proyecto están **por verificar**. TX/RX indican posibles usos, no componentes ya instalados.

| ID | Componente e identificación | Función posible | Características que deben verificarse | Utilidad inicial |
|---|---|---|---|---|
| H01 · F01 | Raspberry Pi de familia Zero, coherente con la consigna; variante exacta no confirmada | Procesar imagen, controlar radio y periféricos | Serigrafía/revisión por ambas caras, conectores, estado de cabecera GPIO, arranque, microSD, OS, SPI y disponibilidad de plataformas para ambos extremos | **Prioritaria TX/RX**: una plataforma por extremo como necesidad de diseño, no cantidad existente |
| H02 · F03 | Módulo RF con conector coaxial, candidato de la familia nRF24 declarada en consigna | Enlace digital de bajo nivel | Chip y placa, nRF24L01 frente a «+» o compatible, presencia real de PA/LNA, pinout, tensión, consumo, antena, homologación y prueba SPI/enlace | **Prioritario TX/RX**; adaptar diseño al módulo existente antes de buscar reemplazos |
| H03 · F02/F03 | Antena articulada y conectores RF | Radiación/recepción | Referencia, frecuencia, ganancia, impedancia, tipo SMA/RP-SMA y contacto central, compatibilidad con módulo; no identificar conector solo por rosca | Usar en radio existente si resulta compatible; no asignar ganancia ni alcance por apariencia |
| H04 · F04 | Convertidor de alimentación con USB-A, función elevadora/reguladora posible | Obtener alimentación desde una fuente autónoma | Referencia, rango de entrada, tensión real de salida, corriente bajo carga/picos, eficiencia, rizado, polaridad, protecciones y si incluye carga de batería | Candidato para alimentar Pi; **no** asumir que sirve directamente para radio o que carga baterías |
| H05 · F07 | Interfaz microSD con señales SPI | Acceso a archivos extraíbles | Modelo, regulación y adaptación de niveles, pinout, tarjeta compatible, consumo y lectura/escritura | Reserva TX/RX; preferir inicialmente ranura integrada de Pi y evitar cableado/dependencias redundantes |
| H06 · F09/F10 | Cables USB y adaptador/empaque micro-USB OTG | Alimentación, configuración y memoria USB | Contenido real del empaque, tipo de conector de cada cable, datos frente a solo carga, continuidad y caída de tensión | Reutilizar para alimentación y preparación; OTG solo si se elige almacenamiento USB |
| H07 · F09/F10 | Adaptadores y cables de vídeo de distintos formatos | Conectar pantalla al RX o monitor durante preparación | Identificar extremos, compatibilidad con salida de Pi, conversión pasiva/activa, alimentación y señal de vídeo real | Evaluar cadena disponible antes de comprar adaptadores; no asumir compatibilidad mini-HDMI |
| H08 · F05/F06 | Placa de audio con jack, compatible visualmente con una interfaz digital de audio | Salida de audio posible | Referencia del integrado, entrada/salida, protocolo, niveles y alimentación | Sin función indispensable en transmisión de imágenes; no integrarla por estar disponible |
| H09 · F08 | Placa circular con símbolo de micrófono, posible interfaz de micrófono digital | Captura de audio posible | Modelo, cara del sensor, dirección de señales, protocolo y tensión | Fuera del alcance inicial; no sustituye cámara ni almacenamiento de imágenes |
| H10 · Fondos F01–F08 | Cables puente, placas de prototipado y material de montaje visibles parcialmente | Montaje de GPIO, controles y alimentación | Separar material, contar, identificar, comprobar continuidad/estado y compatibilidad; el desenfoque impide inventario individual | Aprovechables tras inspección; no dar por confirmados botones, resistencias o condensadores concretos |
| H11 · F11 | Cables, fuentes/adaptadores y equipos audiovisuales; altavoces aparentes | Apoyo de laboratorio o reutilización de conexiones | Etiquetas, salidas, polaridad, conectores, estado y autorización de uso | Revisar cables/fuentes para banco; una fuente de pared no resuelve autonomía. Altavoces no despliegan imágenes |

No se identifica visualmente una pantalla adecuada ni una batería apta. Tampoco se acredita la presencia de tarjetas microSD instaladas por observar una ranura. El gabinete no permite inferir una cámara utilizable ni modelos de los equipos parcialmente ocultos.

## Solución inicial con el material existente

| Subsistema | Aprovechamiento prioritario | Condición para seleccionarlo |
|---|---|---|
| Procesamiento TX/RX | Plataformas Zero H01 | Contar y probar plataformas suficientes, respetando un solo módulo programable por dispositivo |
| Radio TX/RX | Módulos H02 y antenas H03 | Identificar variantes compatibles, pinout, energía y configuración regulatoria; probar comunicación local |
| Archivos | Almacenamiento local de Pi; H05/H06 como alternativas | Verificar tarjetas; usar lector externo o USB solo si resuelve una necesidad concreta |
| Alimentación | Evaluar H04 y cables H06 con fuente autónoma adecuada | Medir salida bajo carga; comprobar si se necesita regulación separada del radio |
| Despliegue RX | Buscar pantalla del laboratorio y aprovechar H07 | Confirmar interfaz, autonomía y uso como periférico, sin agregar otra plataforma programable |
| Controles y montaje | Revisar material H10 | Botón/interruptor y actividad luminosa en ambos; selector/indicación de modo TX y componentes eléctricos adecuados |

CC1101 y óptica/IR se mantienen como alternativas investigadas, no como compras previstas. No adquirir otros radios, amplificadores, lectores o módulos de audio antes de diagnosticar y aprovechar el equipo existente. Los detalles eléctricos y el pinout propuesto se mantienen en el [README de hardware](README.md); este inventario no autoriza cablear una placa aún no identificada.

## Necesidades indispensables y faltantes por comprobar

«No confirmado» no significa «ausente»: primero revisar existencias y opciones de préstamo. No hay una lista de compra aprobada.

| Necesidad | Evidencia disponible | Acción antes de considerar adquisición |
|---|---|---|
| Plataformas y radios para ambos extremos | Familias presentes; cantidades/estado desconocidos | Contar, reservar y probar material H01/H02; reparar o sustituir solo unidades con diagnóstico |
| Energía autónoma de cada dispositivo | Baterías no identificadas; H04 candidato a conversión | Buscar baterías/bancos protegidos y alimentación de pantalla; medir carga y duración antes de dimensionar faltante |
| Regulación y desacoplamiento adecuados al radio | Reguladores declarados; modelo H04 pendiente | Revisar reguladores y condensadores existentes; conseguir únicamente lo que falte para estabilidad verificada |
| Medio de almacenamiento para cada plataforma | Ranuras/interfaz visibles, tarjetas no acreditadas | Verificar tarjetas prestables, capacidad, integridad y arranque |
| Pantalla y conexión para RX | Adaptadores disponibles; pantalla no confirmada | Localizar pantalla compatible y evaluar alimentación autónoma; definir aceptación docente antes de compra |
| Inicio y señalización en ambos extremos, selección/indicación de modo TX | Piezas concretas no identificadas | Revisar botones, LED, resistencias y cableado en laboratorio; completar solo faltantes |
| Cableado y montaje fiables | Material visible parcialmente | Reutilizar piezas compatibles, sustituir dañadas y resolver fijación/aislamiento según montaje |

Cámara, micrófono, altavoces, segundo procesador por extremo y lector microSD externo no son necesidades indispensables del diseño inicial. La consigna permite leer imágenes ya almacenadas en memoria local.

## Registro durante la visita al laboratorio

Para cada unidad, completar: ID de inventario físico, fotografía legible de ambas caras/etiqueta, fabricante/modelo/revisión, cantidad contada, disponibilidad/préstamo, accesorios compatibles, ficha técnica, tensión/pinout, prueba realizada, resultado, fecha y responsable. Mantener estados separados: **existente**, **identificado**, **probado** y **asignado**. Registrar una avería como resultado de prueba, no como deducción visual.

Primero identificar sin energizar; después comprobar alimentación, arrancar las Pi y validar SPI con radio correctamente identificado. Las pruebas de enlace y autonomía se ejecutarán conforme al [plan de evaluación](../../transmision/pruebas/README.md). Hasta entonces no se declara ningún componente funcional ni un transmisor/receptor completo.

Fuentes: fotografías vinculadas, confirmación del equipo en esta iteración y [consigna original](../consigna/escenario_original.pdf). Las propiedades de familias tecnológicas usadas en el diseño se consultan en el [catálogo técnico](../investigacion/fuentes.md); no se trasladan automáticamente al módulo fotografiado.
