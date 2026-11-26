# ProyectoComu

Proyecto del curso IE0527 Ingeniería de Comunicaciones de la UCR: **transmisión inalámbrica de imágenes con codificación de fuente**.

TX es una Raspberry Pi Zero W (`lobo@comu-tx.local`) y RX una Raspberry Pi 4 B (`lobor@comu-rx.local`). El equipo confirmó la primera transmisión real de `HOLA COMU`, con recepción correcta y `ACK=True`, usando `~/prueba_radio.py` y pyRF24 en `~/comu-venv` de cada placa. Esa prueba se conserva; sus archivos remotos no forman parte de este repositorio.

La interfaz Flask permite seleccionar imagen y algoritmo, probar la compresión local
y solicitar el envío por nRF24. Un proceso separado posee el radio, fragmenta el
archivo y confirma la reconstrucción en RX. Se integraron Huffman y cuantización
del equipo; consultar [instalación y pruebas reales](integracion/IMAGENES.md).
Cada Pi sirve su interfaz al teléfono, sin servidor en la PC ni recursos de Internet.

## Estado y guías de trabajo — 26 de noviembre de 2026

La integración completa transmite y reconstruye imágenes con Huffman sin pérdidas
y cuantización con pérdidas. RX conserva una galería con borrado individual; TX
permite borrar fuentes. Probar compresión local es opcional. Se retiró el corte
global de 60 s y se aceleró la preparación Huffman, manteniendo reintentos por trama.

El equipo reportó funcionamiento satisfactorio de **ambos modos a unos 25 m**.
«10/10» describe su valoración, no diez ensayos contados. Consultar el
[registro de campo](documentacion/pruebas/2026-11-26-campo-25m/README.md).
El siguiente trabajo es comprobar y habilitar los controles físicos con `--gpio`;
no se considera que la prueba de radio valide automáticamente los LED y botones.

| Necesidad | Documento |
|---|---|
| Usar, diagnosticar y reiniciar el sistema | [Guía de operación](documentacion/operacion.md) |
| Montar LED, botón y DIP | [Guía breve de hardware](documentacion/hardware/guia_led_botones.md) |
| Entender el recorrido y cada archivo principal | [Arquitectura de software](documentacion/arquitectura_software.md) |
| Evidencias y antecedentes | [Índice de documentación](documentacion/README.md) |

## Documentación técnica

- [Primer avance](documentacion/primer_avance.md): requisitos y diseño histórico.
- [Investigación](documentacion/investigacion/README.md): nRF24, bibliotecas, alternativas, enlace y fuentes.
- [Hardware](documentacion/hardware/README.md) e [inventario](documentacion/hardware/inventario.md): componentes del laboratorio y conexión propuesta.
- [Protocolo](transmision/protocolo/README.md): formato implementado, confirmaciones y errores.
- [Integración](integracion/README.md): controles físicos e interfaz web.
- [Flask local](integracion/web/README.md): API, almacenamiento y ejecución local.
- [Redes de operación](documentacion/despliegue/redes_definitivas.md): direcciones de las interfaces, SSH y recuperación manual.

El equipo confirmó conexión de teléfono/tablet y carga BMP usando el AP abierto de TX.
La decisión final es `Comu-TX` (`192.168.50.1`) y `Comu-RX` (`192.168.60.1`), abiertos,
con DHCP y HTTP 8080. La [migración persistente](integracion/web/RED_LOCAL.md) conserva
la red anterior y protege el primer reinicio con recuperación automática. Ambas
Raspberry superaron por separado la prueba de arranque, acceso desde teléfono y
retorno a PISO 3. El 26 de noviembre, a petición del equipo, se aplicó la
autoconexión permanente de ambos AP y se solicitó su activación, sin retorno
automático. Después de la optimización de software se preparó nuevamente la
activación permanente y el equipo reportó éxito en campo con ambos modos.
El perfil PISO 3 y la recuperación manual se conservan. Quedan la validación
final de GPIO, una medición documentada a 30 m y la autonomía.
