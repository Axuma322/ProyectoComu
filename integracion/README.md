# Integración

Esta carpeta reúne la web local, el proceso que posee el radio, los controles
físicos opcionales y las herramientas de despliegue. TX es una Zero W (`lobo`)
y RX una Pi 4 B (`lobor`). Imágenes y códecs están integrados y probados.

| Archivo o carpeta | Responsabilidad |
|---|---|
| `enlace.py` | Único proceso de imágenes que abre nRF24; consume la cola en TX, reconstruye en RX y controla GPIO con `--gpio` |
| `web/` | Flask + Waitress, páginas, API, almacenamiento y selección; no abre radio ni GPIO |
| `web/trabajos.py` | Cola local, bloqueo entre botón y web y estado con heartbeat |
| `hw_test.py` | Prueba separada de LED, botón y DIP; no transmite |
| `instalar_imagenes.sh` | Instalador del paquete previamente probado; respaldo y comprobación de servicios |
| `web/red_local.py` | Migración explícita y recuperación de AP; requiere root |
| `web/diagnostico_ap.py` | Observador de asociación, DHCP, HTTP y eventos; solo lectura |
| `web/comu-*.service`, `web/comu-*.timer` | Plantillas systemd de web, enlace y ensayo de red |

Para trabajar en esta carpeta:

- [Arquitectura y recorrido de una imagen](../documentacion/arquitectura_software.md).
- [Guía breve de LED, botón y DIP](../documentacion/hardware/guia_led_botones.md).
- [Web y API](web/README.md).
- [Instalación, algoritmos y pruebas reales](IMAGENES.md).
- [Operación y activación persistente de GPIO](../documentacion/operacion.md).

`hw_test.py` y `integracion.enlace --gpio` usan los mismos pines. Detener el
servicio de enlace antes de ejecutar la prueba; la web puede seguir activa.
Los bancos y montajes antiguos se conservan como antecedentes, sin considerarlos
validación de los GPIO en los dos equipos actuales.
