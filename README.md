# ProyectoComu

Proyecto del curso IE0527 Ingeniería de Comunicaciones de la UCR: **transmisión inalámbrica de imágenes con codificación de fuente**.

TX es una Raspberry Pi Zero W (`lobo@comu-tx.local`) y RX una Raspberry Pi 4 B (`lobor@comu-rx.local`). El equipo confirmó la primera transmisión real de `HOLA COMU`, con recepción correcta y `ACK=True`, usando `~/prueba_radio.py` y pyRF24 en `~/comu-venv` de cada placa. Esa prueba se conserva; sus archivos remotos no forman parte de este repositorio.

La interfaz Flask permite seleccionar imagen y algoritmo, probar la compresión local
y solicitar el envío por nRF24. Un proceso separado posee el radio, fragmenta el
archivo y confirma la reconstrucción en RX. Se integraron Huffman y cuantización
del equipo; consultar [instalación y pruebas reales](integracion/IMAGENES.md).
Cada Pi sirve su interfaz al teléfono, sin servidor en la PC ni recursos de Internet.

## Documentación

- [Primer avance](documentacion/primer_avance.md): decisiones y próximos pasos.
- [Investigación](documentacion/investigacion/README.md): nRF24, bibliotecas, alternativas, enlace y fuentes.
- [Hardware](documentacion/hardware/README.md) e [inventario](documentacion/hardware/inventario.md): componentes del laboratorio y conexión propuesta.
- [Protocolo](transmision/protocolo/README.md): paquetes, confirmaciones y pruebas iniciales.
- [Integración](integracion/README.md): controles físicos e interfaz web.
- [Flask local](integracion/web/README.md): instalación, comandos TX/RX y prueba con Android usando la red actual.
- [Redes de operación](documentacion/despliegue/redes_definitivas.md): direcciones de las interfaces, SSH y recuperación manual.

El equipo confirmó conexión de teléfono/tablet y carga BMP usando el AP abierto de TX.
La decisión final es `Comu-TX` (`192.168.50.1`) y `Comu-RX` (`192.168.60.1`), abiertos,
con DHCP y HTTP 8080. La [migración persistente](integracion/web/RED_LOCAL.md) conserva
la red anterior y protege el primer reinicio con recuperación automática. Ambas
Raspberry superaron por separado la prueba de arranque, acceso desde teléfono y
retorno a PISO 3. El 26 de noviembre, a petición del equipo, se aplicó la
autoconexión permanente de ambos AP y se solicitó su activación, sin retorno
automático. TX quedó comprobada desde el teléfono; falta la comprobación final
de RX. El perfil PISO 3 y la recuperación manual se conservan.
La integración de imágenes se probó en las Raspberry con ambos algoritmos;
quedan los controles físicos y las pruebas de transmisión con ambos AP activos,
alcance y autonomía.
