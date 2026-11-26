# Documentación de ProyectoComu

Revisión del 26 de noviembre de 2026. Para trabajar en el sistema actual:

| Documento | Contenido |
|---|---|
| [Operación](operacion.md) | Teléfonos, SSH, servicios, recuperación y GPIO persistentes |
| [Arquitectura](arquitectura_software.md) | Recorrido, módulos, almacenamiento y métricas |
| [LED, botón y DIP](hardware/guia_led_botones.md) | Guía breve para quienes montan los controles |
| [Redes definitivas](despliegue/redes_definitivas.md) | AP permanentes y vuelta a PISO 3 |
| [Integración de imágenes](../integracion/IMAGENES.md) | Algoritmos, dependencias, instalador y pruebas |
| [Protocolo](../transmision/protocolo/README.md) | Tramas, ACK, verificación y errores |
| [Hardware](hardware/README.md) e [inventario](hardware/inventario.md) | Montaje y evidencia de componentes |

## Evidencias

- [Tres imágenes en ambos modos](pruebas/2026-11-26-tres-imagenes/README.md):
  entradas, hashes, seis resultados y vistas recibidas.
- [Sin corte global y Huffman optimizado](pruebas/2026-11-26-sin-limite/README.md):
  mediciones antes/después, 27 pruebas por placa y dos envíos reales posteriores.
- [Campo a unos 25 m](pruebas/2026-11-26-campo-25m/README.md): reporte del equipo,
  separado de las mediciones instrumentadas.

Los registros previos conservan sus condiciones y resultados originales.

## Antecedentes

- [Primer avance](primer_avance.md) e [investigación](investigacion/README.md):
  requisitos y alternativas iniciales.
- [Protocolo preliminar](investigacion/protocolo_preliminar.md): ventanas y
  BLOCK_ACK propuestos, distintos del stop-and-wait implementado.
- [Diagnóstico WPA2](despliegue/antecedentes_ap_wpa2.md): observaciones y propuestas
  anteriores a la decisión de usar redes abiertas.
- [Migración reversible](../integracion/web/RED_LOCAL.md): ensayo inicial de
  arranque con recuperación; el modo permanente no usa ese retorno automático.
