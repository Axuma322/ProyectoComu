# Matriz de trazabilidad

Fuente: [consigna original](escenario_original.pdf), ocho páginas completas. Estado de todas las verificaciones de implementación: **pendiente**. O = obligatorio; Op = optimización opcional; R = recomendación; I = información/recurso, no obligación de consumirlo. Los IDs C corresponden a la numeración original; los demás identifican párrafos sin número. Los enlaces de diseño son [protocolo](../../transmision/protocolo/README.md), [pruebas](../../transmision/pruebas/README.md), [hardware](../hardware/README.md) e [investigación](../investigacion/README.md).

| ID / página | Requisito resumido | Clase | Solución prevista | Verificación / evidencia futura |
|---|---|---|---|---|
| EQ1 / 1 | Equipo de 7–9 personas | O | Registrar integrantes | Lista validada |
| EQ2 / 1–2 | Liderazgo, supervisión técnica y comunicación; decisiones consensuadas y responsabilidades adicionales | O | Asignación de tres roles y acuerdos | Acta de asignación y seguimiento |
| EQ3 / 2 | Todos participan en desarrollo y comunicación | O | Distribuir trabajo y revisiones | Bitácora individual y coevaluación |
| GEN1 / 1 | Consultas docentes puntuales y claras | R | Lista de consultas técnicas | Respuestas archivadas |
| GEN2 / 1 | Documentación original y atribución; no plagio | O | Referencias verificables | Revisión de citas y autoría |
| TEC1 / 2 | Resolver escenario y parámetros | O | Arquitectura y aceptación escalonada | Prueba integral |
| TEC2 / 2 | Alternativas, diseño fundamentado, implementación y evaluación | O | Comparativa y fases | Revisión de diseño y resultados posteriores |
| TEC3 / 2 | Basarse en estándar o norma | O | UIT-R P.525 y PNAF; GFSK/ESB documentados | Docente valida alcance de norma elegida; no afirmar certificación IEEE |
| TEC4 / 2 | Explicitar codificación, modulación, acceso y enlace | O | Fuente futura, GFSK, turnos punto a punto y presupuesto | Informe y configuración real |
| COM1 / 2 | Anteproyecto e informe PDF | O | Ampliar avance y exportar posteriormente | PDFs completos entregados |
| COM2 / 2 | Presentación en lecciones por integrantes | O | Preparar exposición | Presentación y asistencia |
| COM3 / 2 | Bitácora cotidiana | O | `documentacion/bitacora.md` como inicio | Entradas fechadas y aportes |
| C1 / 2 | TX y RX inalámbricos | O | Dos extremos radio | Enlace sin cable de datos |
| C2 / 2 | Máximo un módulo con microprocesador por dispositivo | O | Una Pi por extremo y periféricos | Inspección de diagrama y montaje |
| C3 / 2 | Autonomía temporal sin energía externa | O | Batería por dispositivo | Prueba desconectada, incluida pantalla |
| C4a / 2 | Botón/interruptor y al menos una luz de actividad en ambos | O | GPIO y LED | Demostrar inicio y actividad |
| C4b / 2 | Señales TX/RX/final diferenciadas | R | Patrones de LED | Observación por estado |
| C5 / 2 | Solo bandas no licenciadas u ópticas | O | Subbanda autorizada y equipo verificado | Expediente regulatorio y parámetros |
| C6 / 3 | Prohibidos WiFi, BT, BLE, Zigbee, LoRaWAN, celular | O | Radio bajo nivel, sin pila de red | Inspección de dependencias y operación |
| C7 / 3 | Implementación directa de transmisión digital | O | RF24 driver + protocolo propio | Revisar capas y tramas |
| C8 / 3 | Extraer BMP/PGM sin comprimir, gris, hasta 320×240, de memoria local o extraíble | O | Validación de archivo local Pi | Casos válidos, corruptos y fuera de límites |
| C9 / 3 | Reconstruir, escribir y desplegar | O | Buffer, almacenamiento y pantalla RX | Comparar archivo y observar pantalla |
| C10 / 3 | Dos modos: sin pérdidas exacto y con pérdidas controladas | O | Interfaz de códec futura | Identidad y PSNR según modo |
| C11 / 3 | Selección antes de transmitir e indicación del modo | O | Selector TX, LED y metadata | Cambiar selector, comprobar log y trama |
| C12 / 3 | RX preparado sin saber inicio | O | Escucha RX tras armado | Inicio aleatorio sin aviso al RX |
| C13 / 3 | Reporte final por transferencia | O | Resumen y log | Tabla completa con método y límites |
| FU1 / 3 | Al menos un códec sin pérdidas y uno con pérdidas explicados | O | Estudio posterior, sin implementación ahora | Fundamento y pruebas reversibles/distorsión |
| FU2 / 3 | Al menos cuatro puntos con pérdidas y curva tasa-distorsión | O | Barrido de parámetros posterior | Cuatro puntos por imagen y gráficas |
| C14 / 4 | Comparar ahorro de tiempo y compresión | O | Baseline sin comprimir | Tabla de tiempos y razones |
| C15 / 4 | Umbral perceptible e inaceptable | O | Evaluación visual con criterio y PSNR | Imágenes comparadas y juicio documentado |
| C16 / 4 | Costo de comprimir/descodificar y punto de compensación | O | Medición por etapa | Balance tiempo total vs baseline |
| C17 / 4 | Recomendación de esquema y criterio | O | Conclusión basada en datos | Comparativa multicriterio |
| C18 / 4 | Efecto de fotografía/sintética/áreas uniformes | O | Ensayar tres clases | Resultados diferenciados |
| M1 / 4 | Tamaños original/transmitido y razón | O | Contabilidad definida en pruebas | Logs por intento, incluir cabeceras |
| M2 / 4 | Sobrecarga incluyendo reintentos | O | Desglose por capa/dirección | Contadores e incertidumbre RF |
| M3 / 4 | Tiempos de compresión, transmisión, descompresión y total | O | Relojes monotónicos y base común externa | Intervalos con definición de extremos |
| M4 / 4 | Tasa útil | O | Original/total | Recalcular desde registro |
| M5 / 4 | BER | O; método pendiente | Consulta docente e instrumentación | No sustituir por PER; N/D explicado si no observable |
| M6 / 4 | PSNR; sin pérdidas infinito y diferencia cero | O | Comparación de raster y archivo | MSE cero o PSNR medido |
| M7 / 4 | SSIM | Op | Decidir utilidad | Versión/parámetros si se adopta |
| C19 / 4 | Laboratorio 201 IE con horario acordado | I / O si se usa | Reservar sesión | Confirmación de horario |
| C20 / 4 | Pi Zero, nRF24L01, reguladores, cables y Linux disponibles | I | Inventario preliminar | Inspección física y conteo; no dar por entregado |
| C21 / 4 | Consultas y posible inducción | I | Solicitar si hace falta | Registro de consulta |
| C22 / 4 | Se proporcionarán imágenes de prueba | I | Esperar originales oficiales | Archivos/digests recibidos |
| C23 / 5 | Tres imágenes: foto, uniforme y detalle fino | O | Banco de pruebas | Identificar tres clases |
| C24 / 5 | Modo indicado antes de prueba | O | Registrar modo solicitado | Selector/metadata coincide |
| C25 / 5 | Distancia 30 m LOS | O | Demostración medida | Distancia, orientación y condiciones |
| C26 / 5 | RX desconoce inicio | O | Escucha independiente | Observación sin sincronizar botón RX |
| C27 / 5 | Hasta tres intentos, intervalos de 5 min | Condición | Programación de ensayos | Marcas e intentos, conservar fallos |
| MIN1 / 5 | Al menos dos de tres imágenes correctas | O | Transferencia con verificación | Conteo de éxitos bajo condiciones oficiales |
| MIN2 / 5 | Modo sin pérdidas bit a bit idéntico | O | Preservar archivo y raster | Comparación exacta y SHA-256 |
| MIN3 / 5 | Con pérdidas reconocible y PSNR >25 dB | O | Ajustar códec futuro | Inspección y cálculo con referencia |
| MIN4 / 5 | Tiempo total no superior a 60 s por intento | O | Deadline y medición integral | Botón→despliegue; criterio conservador por aclarar |
| MIN5 / 5 | Métricas al finalizar | O | Tabla por éxito/fallo | Auditoría del registro |
| C28 / 5 | Compresión sin pérdidas >2:1 | Op | Optimizar después | Razón según capa acordada |
| C29 / 5 | PSNR >35 dB y compresión con pérdidas >10:1 | Op | Explorar códec | Ambos umbrales simultáneos |
| C30 / 5 | Tres imágenes en <20 s total | Op | Optimizar integración | Tiempo conjunto, no cada imagen |
| C31 / 5 | Sobrecarga <20 % | Op | Revisar encapsulación; no resuelto | Contabilidad con capa acordada |
| C32 / 5 | Curva con cuatro puntos sobre enlace real | Op adicional | Repetir barrido físicamente | Logs RF; FU2 ya obliga curva general |
| C33 / 5 | Selección automática por características | Op | Etapa posterior justificada | Criterio y casos de decisión |
| C34 / 5 | Tres imágenes a 100 m LOS | Op | Extensión tras 30 m | Prueba de distancia |
| C35 / 5 | Tres imágenes a 50 m con obstáculos sin LOS | Op | Extensión con entorno documentado | Fotografías/registro de obstáculos |
| ENT1 / 5–6 | Análisis técnico del escenario/desafíos | O | Avance e investigación | Revisión de documento |
| ENT2 / 5–6 | Similares, norma, alternativas y selección | O | Casos de fabricante, RF24 y P.525; ampliar casos académicos luego | Bibliografía y comparación |
| ENT3 / 6 | Fundamento de fuente, comparativa, cuadros, curva y respuestas | O | Secciones reservadas, metodología | Informe con datos reales posteriores |
| ENT4 / 6 | Presupuesto y cronograma | O | Inventario/cotizaciones y semanas | Costos reales y calendario de equipo |
| ENT5 / 6 | Procedimiento, resultados, conclusiones y recomendaciones | O | Plan y futura evaluación | Informe final sin hipótesis presentadas como resultados |
| ENT6 / 6 | Demostración de funcionamiento final | O | Guion de prueba integral | Demostración y señales por etapa |
| CAL / 6 | Semanas 7–13 y entregas | O organizativa | Plan relativo en bitácora | Fechas reales por confirmar con curso |
| EVA1 / 7 | Coevaluación de otros equipos y evaluación docente | O | Reservar revisión cruzada | Formularios/presentaciones |
| EVA2 / 7–8 | Roles y sinergia; nota individual ponderada | O organizativa | Evidencia de aportes | Evaluación individual y grupal |

## Observaciones de interpretación

El mínimo menciona inicio de transmisión→recepción/demostración, mientras la métrica total exige botón→despliegue. Se adopta provisionalmente el criterio más estricto, botón→despliegue ≤60 s, y se solicita confirmación. Una curva con cuatro puntos es obligatoria (FU2); medirla sobre enlace real es optimización C32.

El cuadro de evaluación de solución (p. 7) imprime totales 24 % +65 % frente a 100 %, y el de trabajo (p. 8) tiene columnas de 70 % y 100 %. Hay inconsistencias aparentes: no corregir ni renormalizar sin consulta. La fórmula expresa solución × trabajo en equipo. Conservar PDF como autoridad y confirmar rúbrica con docente. Los esquemas de comunicaciones y resultados tienen peso destacado en el cuadro: deben sostenerse con configuración y evidencia, no solo narrativa.
