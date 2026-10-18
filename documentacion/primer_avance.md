# Primer avance: investigación y diseño preliminar

IE0527 Ingeniería de Comunicaciones — Universidad de Costa Rica. Fecha: 16 de octubre de 2026. Estado: propuesta documental, sin sistema implementado ni mediciones de radio.

## 1. Introducción y escenario

El proyecto transportará imágenes digitales entre dos dispositivos portátiles y evaluará cómo la codificación de fuente modifica tamaño, tiempo y fidelidad. Se leyó íntegramente la [consigna de ocho páginas](consigna/escenario_original.pdf), incluidas evaluación, cronograma y optimizaciones. La [matriz de trazabilidad](consigna/matriz_requisitos.md) enlaza obligaciones y procedimientos de verificación. El equipo confirmó que los componentes fotografiados existen físicamente en el laboratorio. El [inventario visual](hardware/inventario.md) documenta su aprovechamiento prioritario; modelos, cantidades, disponibilidad y funcionamiento siguen pendientes, sin acreditar todavía dos conjuntos completos.

## 2. Problema técnico y restricciones

El sistema debe usar una sola plataforma programable por extremo, energía autónoma, botón y actividad luminosa; leer BMP/PGM gris sin comprimir hasta 320×240, transmitir por enlace de bajo nivel, reconstruir, guardar y desplegar. El receptor debe esperar sin conocer inicio. Quedan excluidos WiFi, Bluetooth/BLE, Zigbee, LoRaWAN y redes celulares. Selección de modo con/sin pérdidas antes de iniciar e indicación visible son obligatorias. [C](investigacion/fuentes.md)

La prueba mínima es 30 m con línea de vista y al menos dos de tres imágenes correctas; sin pérdidas exige identidad exacta, con pérdidas imagen reconocible y PSNR >25 dB. Se adopta provisionalmente ≤60 s desde botón hasta despliegue para resolver conservadoramente la diferencia de redacción de los intervalos. 

## 3. Investigación de alternativas

La [comparación completa](investigacion/alternativas.md) evalúa Pi Zero+nRF24L01+, CC1101 y óptica/IR. La primera ofrece un controlador documentado y disponibilidad declarada. CC1101 ofrece flexibilidad sub-GHz y CCA, pero demanda seleccionar perfil RF y banda local. Óptica evita dependencia del espectro RF, a cambio de alineación, sensibilidad a luz ambiente y electrónica/temporización todavía sin dimensionar. Las notas de aplicación de TI/Vishay y ejemplos RF24 son antecedentes técnicos de enlaces similares, no evidencia de que nuestro montaje cumpla la consigna. [N, T, V, RE](investigacion/fuentes.md)

## 4. Comparación y selección preliminar

Se recomienda Pi Zero y radio nRF24, condicionado a identificar modelo y variante. La decisión prioriza materiales declarados, SPI y facilidad de prueba; no una promesa de alcance comercial. Se propone estudiar 1 Mbit/s como punto inicial y contrastar tasas según sensibilidad y tiempo efectivo. Si el chip es nRF24L01 sin «+», revisar configuración y descartar 250 kbit/s. PA/LNA no se presupone por la presencia de conector SMA. [Investigación de radio](investigacion/nrf24.md)

## 5. Arquitectura general

Una Pi por extremo realiza todas las funciones de aplicación. El radio, regulador, botones, LED, almacenamiento y pantalla se conectan como periféricos. La pantalla y la energía siguen sin seleccionar; no añadir segunda Pi/Arduino para la interfaz. El [documento de protocolo](../transmision/protocolo/README.md) incluye diagrama Mermaid de recorrido y estados TX/RX; [hardware](hardware/README.md) contiene pinout, inventario y límites eléctricos.

La separación de módulos permite integrar después el códec mediante flujo de bytes, algoritmo, parámetros y tamaños. El receptor valida íntegramente el flujo antes de reconstruir y mostrar. Se parte de memoria local permitida; cámara no es requisito verificado.

## 6. Fundamento de comunicación

GFSK desplaza la frecuencia de portadora según símbolos filtrados; el nRF24 proporciona empaquetado y transacciones Enhanced ShockBurst. La biblioteca RF24 controla SPI/GPIO y registros. Chip, placa comercial y biblioteca son niveles distintos: potencia y corriente de una placa PA/LNA no se deducen de la ficha del chip. No se emplean RF24Network, Mesh, Gateway ni TCP/IP. [N, R, RL, RP](investigacion/fuentes.md)

## 7. Protocolo conceptual

Se propone sesión identificada con START/META, READY, DATA numerado, confirmación de bloques, FIN, RESULT y cancelación. El radio aporta CRC/ACK/reintentos por paquete; la aplicación añade límites, metadata, reensamblado, duplicados, plazos y verificación completa. Un ACK RF no demuestra que el archivo fue guardado. Acceso semidúplex por turnos con un iniciador, sin atribuir CSMA/CA. El diseño contempla repetir FIN para recuperar RESULT perdido y reiniciar sesiones fallidas con ID nuevo. [Detalle y estados](../transmision/protocolo/README.md)

## 8. Normas y presupuesto de enlace

Se usa UIT-R P.525 como referencia de propagación en espacio libre y PNAF/SUTEL para condiciones nacionales, sin presentar ESB como certificación de una norma IEEE. Debe confirmarse con el profesor si ese conjunto satisface su expectativa de norma de referencia. Se verificó reforma 45769-MICITT de abril de 2026, posterior a la copia consolidada MICITT consultada. El expediente regulatorio queda abierto hasta confirmar versión vigente y certificado/configuración del módulo. [Normativa y cálculos](investigacion/normativa_enlace.md), [L, L26, S, U](investigacion/fuentes.md)

El escenario analítico explícito con 2440 MHz, potencia de chip 0 dBm, antenas ideales de 0 dBi y pérdidas adicionales supuestas permite estudiar margen a 30/100 m. No demuestra alcance, interferencia tolerable ni duración real. El [script sin dependencias](investigacion/calculos_preliminares.py) reproduce pérdidas, márgenes y escenarios de fragmentación/latencia. El diseño inicial no resuelve la optimización de sobrecarga <20 %.

## 9. Metodología de implementación y pruebas

El [plan de evaluación](../transmision/pruebas/README.md) avanza desde enlace local y datos conocidos a bloques, archivos sin compresión, imágenes, códecs y distancia. Define criterios de éxito, registros y medidas de tiempo sin restar relojes no sincronizados. Se medirá tamaño original y transmitido, sobrecarga/reintentos, tiempos por etapa y total, tasa útil y PSNR; SSIM es opcional. Deben compararse al menos cuatro puntos con pérdidas y responder preguntas C14–18; no se implementan algoritmos ahora.

BER requiere acuerdo docente: el descarte CRC impide observar el flujo físico erróneo desde ESB normal. PER, reintentos y BER residual condicionada no sustituyen BER físico. También se debe acordar la capa de contabilidad del tráfico y tratamiento de ACK no observables. Los logs conservarán fallos y valores no disponibles con explicación, sin cifras inventadas.

## 10. Riesgos y actividades pendientes

| Riesgo / incertidumbre | Mitigación prevista | Información y decisión requerida |
|---|---|---|
| Placas y cantidad real | Inspección y arranque antes de adquirir accesorios | Modelo de dos Pi, GPIO, almacenamiento y OS |
| Radio falso, variante sin «+» o PA/LNA desconocido | Revisar marcas y registros, obtener ficha del módulo | Referencia, proveedor, dos unidades y antenas |
| Caídas de tensión | Regulación y desacoplamiento junto al radio, medir transitorios | Corriente de picos, rizado, conectores y capacidad de fuente |
| Backend RF24/kernel | Prueba oficial pequeña antes de integrar | Arquitectura Linux, versión RF24 y permisos SPI/GPIO |
| Tasa útil insuficiente | Medir por etapas, limitar bucle crítico y reintentos | Rendimiento host, tasa RF y tamaños de cabecera/bloque |
| Interferencia y orientación | Caracterizar entorno y fijar canal autorizado con registro | Ubicación, canal, ganancia y montaje |
| Autonomía | Medir potencia completa, incluida pantalla y RX continuo | Batería protegida, capacidad Wh y duración requerida |
| Despliegue/almacenamiento | Validar periférico y persistencia con una sola Pi | Pantalla, autonomía y aceptación docente |
| BER y contabilidad RF | Consulta docente e instrumentación adecuada | Métricas aceptadas, punto de medición y capa |
| Regulación | Revisar PNAF consolidado y homologación con laboratorio | Certificado, antena, banda y potencia permitidas |
| Integración de fuente | Contrato versionado y límites de memoria/longitud | Códecs posteriores y referencia para PSNR |
| Tiempo y cooperación | Roles, bitácora y pruebas tempranas | Integrantes, calendario de curso y turnos de laboratorio |

Orden recomendado antes de programar radio propio: confirmar inventario; acordar dudas docentes; cerrar energía/pantalla y revisión regulatoria; seleccionar OS/backend y configuración; aprobar contrato del protocolo y métricas. El [plan por semanas y bitácora](bitacora.md) conserva cronograma original sin inventar fechas ni precios. La rúbrica tiene inconsistencias de totales que requieren aclaración, registradas en la matriz.

## 11. Conclusiones preliminares

La opción nRF24 es la base más justificada con los recursos declarados. La implementación sigue condicionada por identificación de componentes, alimentación, visualización y método de evaluación. La siguiente etapa puede comenzar con un ensayo oficial mínimo y transferencia sin compresión; solo después integrar codificación. Esta entrega establece trazabilidad y criterios de prueba, sin afirmar cumplimiento físico.

## 12. Referencias bibliográficas

[Catálogo de fuentes verificables](investigacion/fuentes.md): consigna UCR (C); Nordic Semiconductor, especificación nRF24L01+ v1.0 (N); RF24/Linux/problemas/ejemplos y pyRF24 (R, RL, RI, RE, RP); Raspberry Pi (P); Texas Instruments CC1101 (T); notas técnicas Vishay (V); UIT-R P.525-5 (U); PNAF 44010-MICITT y reforma 45769-MICITT (L, L26); SUTEL RCS-245-2023 (S). Cada documento de detalle vincula sus fuentes y distingue datos de fabricante, hipótesis y verificaciones pendientes.
