# ProyectoComu

Proyecto del curso IE0527 Ingeniería de Comunicaciones de la UCR: **transmisión inalámbrica de imágenes con codificación de fuente**.

TX es una Raspberry Pi Zero W (`lobo@comu-tx.local`) y RX una Raspberry Pi 4 B (`lobor@comu-rx.local`). El equipo confirmó la primera transmisión real de `HOLA COMU`, con recepción correcta y `ACK=True`, usando `~/prueba_radio.py` y pyRF24 en `~/comu-venv` de cada placa. Esa prueba se conserva; sus archivos remotos no forman parte de este repositorio.

La primera interfaz Flask permite preparar imágenes en TX y consultar el estado de integración en RX. Todavía no envía imágenes ni comprime datos; el enlace entre Raspberry seguirá siendo exclusivamente nRF24. Cada Pi sirve su interfaz al teléfono, sin servidor en la PC ni recursos de Internet.

## Documentación

- [Primer avance](documentacion/primer_avance.md): decisiones y próximos pasos.
- [Investigación](documentacion/investigacion/README.md): nRF24, bibliotecas, alternativas, enlace y fuentes.
- [Hardware](documentacion/hardware/README.md) e [inventario](documentacion/hardware/inventario.md): componentes del laboratorio y conexión propuesta.
- [Protocolo](transmision/protocolo/README.md): paquetes, confirmaciones y pruebas iniciales.
- [Integración](integracion/README.md): controles físicos e interfaz web.
- [Flask local](integracion/web/README.md): instalación, comandos TX/RX y prueba con Android usando la red actual.

No se cambiaron redes ni se habilitaron puntos de acceso o servicios automáticos. La transferencia de archivos y la integración de códecs se realizarán después de validar la interfaz.
