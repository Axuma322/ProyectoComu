# Codificación de fuente

Los algoritmos del equipo están en `transmision/algoritmos/`. Esta carpeta
conserva la separación inicial del proyecto; no contiene otro codificador que
deba ejecutarse para usar la web.

- [Huffman](../transmision/algoritmos/algoritmo_sin_perdidas/README.md): la
  integración HUF2 conserva el archivo original completo.
- [Cuantización](../transmision/algoritmos/con_perdidas/README.md): QPG1 de
  1 a 7 bits por píxel, con reconstrucción PGM.
- [Adaptador y recorrido](../documentacion/arquitectura_software.md):
  `transmision/codecs.py` valida, codifica, reconstruye y calcula métricas antes
  de entregar bytes al protocolo.

Automático compara tamaños y elige un candidato de al menos 25 dB de PSNR o
reconstrucción exacta. Este objetivo del software no sustituye los requisitos
de evaluación del curso. Ver [integración](../integracion/IMAGENES.md).
