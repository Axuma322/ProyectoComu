# ProyectoComu

Proyecto del curso IE0527 Ingeniería de Comunicaciones de la UCR: **transmisión inalámbrica de imágenes con codificación de fuente**.

Estamos investigando la comunicación entre dos Raspberry Pi Zero mediante radios nRF24 del laboratorio. Usaremos una Pi por extremo y un protocolo propio punto a punto. Ya se identificaron los radios (nRF24L01+ con PA/LNA) y se probó la comunicación por SPI con uno de ellos; falta probar el enlace entre dos radios.

El trabajo actual se concentra en la transmisión. La codificación de fuente se integrará después.

## Documentación

- [Primer avance](documentacion/primer_avance.md): decisiones y próximos pasos.
- [Investigación](documentacion/investigacion/README.md): nRF24, bibliotecas, alternativas, enlace y fuentes.
- [Hardware](documentacion/hardware/README.md) e [inventario](documentacion/hardware/inventario.md): componentes del laboratorio y conexión propuesta.
- [Protocolo](transmision/protocolo/README.md): paquetes, confirmaciones y pruebas iniciales.
- [Integración](integracion/README.md): prueba de LED, botón y DIP del transmisor.

Las carpetas de transmisor y receptor están reservadas para sus programas. Esta revisión solo modifica documentación.
