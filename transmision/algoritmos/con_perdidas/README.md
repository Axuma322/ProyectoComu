# Codificador PGM con pérdidas

Instalación: `python -m pip install numpy Pillow`

Ejemplo: `python codificador.py imagenes/01_fotografica.pgm 4 comprimidas/foto.bin`

Pruebas: `python pruebas_codificador.py` (12 combinaciones y pruebas de empaquetado).

Interfaz para transmisión: `from codificador import comprimir_pgm`; `datos = comprimir_pgm(ruta, 4)` devuelve bytes completos.

> **Nota sobre formatos de entrada:** El codificador (`codificador.py`) y la suite de evaluación (`pruebas.py`) aceptan imágenes de entrada tanto en formato `.pgm` como `.bmp` (convirtiéndolas automáticamente a escala de grises de 8 bits si fuera necesario). El decodificador mantiene intacto el contrato `QPG1` y sigue generando archivos `.pgm` (P5).

## Contrato para el decodificador
Cabecera de 9 bytes, struct `>4sHHB`: magia QPG1, ancho uint16 big-endian, alto uint16 big-endian, bits uint8. Luego símbolos cuantizados en orden de filas, MSB primero, sin separación entre símbolos, con ceros de relleno al final hasta completar un byte. Longitud de carga: ceil(ancho*alto*bits/8). Cuantización q = p >> (8-bits). Reconstrucción recomendada: p = (q << (8-bits)) + (1 << (7-bits)); usar enteros suficientemente amplios. Guardar PGM P5 con máximo 255. El archivo .bin no es PGM: es el flujo comprimido propio.

Las pruebas incluyen una inversa de referencia local, no el decodificador de producción. PSNR y razón local no incluyen el enlace inalámbrico. Se incluyen las tres imágenes convertidas y los 12 archivos comprimidos.
