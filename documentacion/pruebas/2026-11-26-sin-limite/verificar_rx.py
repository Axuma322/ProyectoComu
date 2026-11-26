"""Verifica archivos y vistas HTTP en RX, correlacionados por trabajo de TX."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import urllib.request

from PIL import Image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--salida', type=Path, required=True)
    parser.add_argument('--sha256-original', required=True)
    parser.add_argument('trabajos', nargs='+')
    args = parser.parse_args()
    root = Path.home() / '.local/share/proyectocomu-web'
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open('http://127.0.0.1:8080/api/recibidas', timeout=10) as response:
        gallery = json.load(response)['imagenes']
    results = []
    for job in args.trabajos:
        matches = []
        for record in (root / 'recepciones').glob('*.json'):
            receipt = json.loads(record.read_text())
            if receipt['metricas'].get('trabajo') == job:
                matches.append(receipt)
        assert len(matches) == 1, (job, 'La recepción debe existir una sola vez', len(matches))
        receipt = matches[0]
        metrics = receipt['metricas']
        name = receipt['nombre']
        assert Path(name).name == name
        raw = (root / 'recibidas' / name).read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        assert digest == metrics['sha256_reconstruida']
        assert metrics['sha256_original'] == args.sha256_original
        if metrics['modo'] == 'sin_perdidas':
            assert digest == args.sha256_original
        with Image.open(io.BytesIO(raw)) as image:
            image.load()
            size = image.size
            pixels = image.convert('L').tobytes()
        assert size == (metrics['ancho'], metrics['alto'])
        listed = next(item for item in gallery if item['nombre'] == name)
        with opener.open('http://127.0.0.1:8080' + listed['url'], timeout=10) as response:
            assert response.headers['Content-Type'].startswith('image/png')
            png = response.read()
        with Image.open(io.BytesIO(png)) as preview:
            assert preview.size == size
            assert preview.convert('L').tobytes() == pixels
        results.append(dict(trabajo=job, validacion_rx=True,
                            sha256_archivo_rx=digest, vista_http_verificada=True,
                            sha256_vista_png=hashlib.sha256(png).hexdigest(),
                            recepcion=receipt))
        print(json.dumps(dict(trabajo=job, modo=metrics['modo'],
                              validacion_rx=True, ancho=size[0], alto=size[1])), flush=True)
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    args.salida.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
