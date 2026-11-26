# Algoritmo sin pérdidas

Integración: el árbol Huffman y la decodificación de este trabajo se utilizan en
`transmision/codecs.py`. La CLI ahora produce HUF2, que admite 256 símbolos,
dimensiones variables y recuperación exacta del archivo completo, sin asumir
longitudes fijas de encabezados BMP/PGM. Se conserva el código anterior como
referencia (`legacy_main`). Ver [integración](../../../integracion/IMAGENES.md).

Los archivos toman de argumentos dos archivos: uno de entrada y otro de salida, en ese orden. Se llama:  

```Python python compresor_sin_perdidas.py input.bmp compressed.bin``` 

```Python python descompresor_sin_perdidas.py compressed.bin recovered.bmp```

Automáticamente reconoce la extensión (.bmp según el formato del profe (BITMAPINFOHEADER) o .pgm con header P5).
