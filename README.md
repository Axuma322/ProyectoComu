# ProyectoComu

Proyecto integrador IE0527 Ingeniería de Comunicaciones, Universidad de Costa Rica: **transmisión inalámbrica de imágenes con codificación de fuente**.

Estado: investigación y diseño preliminar, 16 de octubre de 2026. No hay transmisor, receptor ni codificadores implementados; tampoco resultados experimentales. Diseño provisional: una Raspberry Pi Zero por extremo, radio nRF24 compatible y protocolo propio punto a punto. 

## Navegación

1. [Primer avance](documentacion/primer_avance.md): síntesis y decisiones.
2. [Consigna original](documentacion/consigna/README.md) y [matriz de trazabilidad](documentacion/consigna/matriz_requisitos.md).
3. [Investigación](documentacion/investigacion/README.md): alternativas, nRF24, normativa, enlace y fuentes.
4. [Hardware](documentacion/hardware/README.md) e [inventario visual](documentacion/hardware/inventario.md): componentes existentes, verificaciones pendientes y conexión propuesta.
5. [Protocolo](transmision/protocolo/README.md): arquitectura, estados y transferencia conceptual.
6. [Evaluación](transmision/pruebas/README.md): fases, métricas y consultas docentes.
7. [Bitácora y planificación](documentacion/bitacora.md).

`transmision/transmisor/`, `transmision/receptor/`, `codificacion/` e `integracion/` reservan las próximas etapas. `recursos/` conserva las fotografías originales y el PDF recibido; la copia documental del PDF se verifica por SHA-256. No se requieren bibliotecas de radio para leer esta investigación.

## Cálculos reproducibles

Con Python 3, sin dependencias externas:

```sh
python documentacion/investigacion/calculos_preliminares.py
```

El script reproduce los escenarios de enlace y capacidad; no controla hardware ni certifica alcance o legalidad. Los documentos contienen enlaces relativos y Mermaid para lectura en GitHub. No se realizaron commits ni push.
