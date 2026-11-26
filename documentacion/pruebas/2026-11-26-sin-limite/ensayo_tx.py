"""Ensayo HTTP de la imagen seleccionada; las imágenes cruzan solo el nRF24.

Ejecutar en TX con los servicios web y de enlace activos en ambas Raspberry.
No cambia radio, redes ni archivos originales. Restaura la selección previa.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import time
import urllib.request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--salida', type=Path, required=True)
    parser.add_argument('--base', default='http://127.0.0.1:8080')
    args = parser.parse_args()
    args.salida.mkdir(parents=True, exist_ok=True)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    html = opener.open(args.base + '/', timeout=10).read().decode()
    token = re.search(r'name="comu-token" content="([^"]+)"', html).group(1)

    def api(route, value=None, post=False):
        request = urllib.request.Request(
            args.base + route,
            data=json.dumps(value).encode() if value is not None else (b'' if post else None),
            headers={'Content-Type': 'application/json', 'X-Comu-Token': token})
        with opener.open(request, timeout=10) as response:
            return json.load(response)

    state = api('/api/estado')
    assert state['enlace']['disponible'], state
    original = state['seleccion']
    assert original, 'Primero selecciona una imagen en TX.'
    source = Path.home() / '.local/share/proyectocomu-web/imagenes' / original['imagen']
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    report = dict(inicio_unix=time.time(), seleccion_original=original,
                  sha256_fuente=source_hash, pruebas=[])
    own_selection = None
    try:
        for mode in ('sin_perdidas', 'con_perdidas'):
            selected = dict(imagen=original['imagen'], modo=mode, bits=original['bits'])
            own_selection = api('/api/seleccion', selected)['seleccion']
            job = api('/api/transmitir', post=True)['trabajo']
            print(json.dumps(dict(modo=mode, trabajo=job)), flush=True)
            started = time.monotonic()
            bucket = -1
            while True:
                state = api('/api/estado')
                link = state['enlace']
                if link.get('trabajo') == job:
                    current = int(link.get('progreso', 0) // 20)
                    if current != bucket:
                        print(json.dumps(dict(modo=mode, estado=link['estado'],
                                              progreso=link.get('progreso'),
                                              observado_s=round(time.monotonic() - started, 2))), flush=True)
                        bucket = current
                    if link['estado'] in {'completado', 'error'}:
                        result = dict(trabajo=job, modo=mode, estado=state,
                                      observado_s=time.monotonic() - started)
                        report['pruebas'].append(result)
                        (args.salida / (mode + '-tx.json')).write_text(
                            json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
                        print(json.dumps(dict(modo=mode, resultado=link['estado'],
                                              metricas=link.get('metricas'), error=link.get('error'))), flush=True)
                        if link['estado'] == 'error':
                            raise RuntimeError(link.get('error'))
                        break
                if time.monotonic() - started > 240:
                    # Es un límite del observador, no cancela el envío del servicio.
                    raise TimeoutError('El observador terminó; la transmisión no fue cancelada.')
                time.sleep(0.5)
            time.sleep(1)
    finally:
        current = api('/api/estado')['seleccion']
        keys = ('imagen', 'modo', 'bits')
        if own_selection and all(current.get(k) == own_selection[k] for k in keys):
            api('/api/seleccion', {k: original[k] for k in keys})
            report['seleccion_restaurada'] = True
        else:
            report['seleccion_restaurada'] = False
        report['fuente_sin_cambios'] = hashlib.sha256(source.read_bytes()).hexdigest() == source_hash
        report['fin_unix'] = time.time()
        (args.salida / 'resumen-tx.json').write_text(
            json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')


if __name__ == '__main__':
    main()
