"""Pruebas locales: inversa de referencia solo para verificar el codificador."""
from pathlib import Path
from time import perf_counter
import numpy as np
from codificador import leer_pgm, comprimir_pgm, CABECERA, empaquetar_bits

BASE = Path(__file__).resolve().parent
assert empaquetar_bits(np.array([9,6], dtype=np.uint8), 4) == b'\x96'
assert empaquetar_bits(np.array([5,2,7], dtype=np.uint8), 3) == b'\xab\x80'
for ruta in sorted((BASE/'imagenes').glob('*.pgm')):
    original = leer_pgm(ruta)
    for bits in (7, 6, 5, 4, 3, 2):
    #for bits in (7,6,4,2):
        t = perf_counter()
        datos = comprimir_pgm(ruta,bits)
        ms = (perf_counter()-t)*1000
        magic,w,h,b = CABECERA.unpack_from(datos)
        assert (magic,w,h,b)==(b'QPG1', original.shape[1],original.shape[0],bits)
        assert len(datos)==9+(w*h*b+7)//8
        flujo = np.unpackbits(np.frombuffer(datos[9:],dtype=np.uint8),bitorder='big')
        assert not flujo[w*h*b:].any()
        q = flujo[:w*h*b].reshape(-1,b) @ (2**np.arange(b-1,-1,-1))
        assert np.array_equal(q,original.ravel()>>(8-b))
        reconstruida = (q*(2**(8-b)) + 2**(7-b)).reshape(h,w)
        mse = np.mean((original.astype(float)-reconstruida)**2)
        psnr = 10*np.log10(255**2/mse) if mse else float('inf')
        salida=BASE/'comprimidas'/f'{ruta.stem}_{bits}bits.bin'
        salida.parent.mkdir(exist_ok=True)
        salida.write_bytes(datos)
        print(f'{ruta.stem:22} {bits} bits {len(datos):6} B RC={ruta.stat().st_size/len(datos):.3f} PSNR={psnr:.2f} dB {ms:.2f} ms')
