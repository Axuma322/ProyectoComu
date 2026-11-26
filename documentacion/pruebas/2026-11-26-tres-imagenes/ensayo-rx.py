"""Observación independiente: archivos recibidos por nRF24, su hash y vista HTTP."""
import hashlib, io, json, re, subprocess, sys, time, urllib.request
from pathlib import Path
from PIL import Image

study = Path(sys.argv[1])
study.mkdir(parents=True,exist_ok=True)
(study/'vistas').mkdir(exist_ok=True)
root = Path.home()/'.local/share/proyectocomu-web'
history = root/'recepciones'
baseline = set(history.glob('*.json')) if history.exists() else set()
seen = set(baseline)
expected = {"02_areas_uniformes.bmp":"d86143bde017996ff46666e0f8ba9bace1942ae28f55eb2a0d84d58c38e072d4","03_detalle_fino.bmp":"8370cfa4b1b7e5f425bba3b3e2e997a04c2e370b6b6d9c57a2ac6e2849dca00d","04_patron_geometrico.bmp":"b6db6f282474aeb2a4245ae7b76f4849cc3d5a5e4701452f5bbfa084a40ec3a9"}
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
started = time.monotonic()
results, power_samples = [], []
while time.monotonic()-started<600 and not (study/'detener-observador').exists():
    raw = subprocess.check_output(['vcgencmd','get_throttled'],text=True,timeout=3).strip()
    flags = int(raw.split('=')[1],16)
    power_samples.append(dict(segundos=round(time.monotonic()-started,2),registro=raw,
                              baja_tension_activa=bool(flags&1),limitacion_activa=bool(flags&4)))
    for record in sorted(history.glob('*.json')) if history.exists() else []:
        if record in seen: continue
        seen.add(record)
        try:
            receipt = json.loads(record.read_text())
            metrics = receipt['metricas']
            label = re.sub(r'^[0-9a-f]{32}_','',metrics.get('nombre',''))
            if label not in expected: continue
            name = receipt['nombre']
            assert Path(name).name==name
            path = root/'recibidas'/name
            raw_image = path.read_bytes()
            digest = hashlib.sha256(raw_image).hexdigest()
            assert digest==metrics['sha256_reconstruida'], 'SHA de reconstrucción no coincide'
            assert metrics['sha256_original']==expected[label], 'No corresponde al original de Windows'
            with Image.open(io.BytesIO(raw_image)) as image:
                assert image.size==(320,240)
                pixels = image.convert('L').tobytes()
            mode = metrics['modo']
            if mode=='sin_perdidas': assert digest==expected[label], 'Archivo sin pérdidas diferente'
            else: assert metrics['mse_tx']==0 or metrics['psnr_tx_db']>25
            url = 'http://127.0.0.1:8080/recibidas/'+name+'/vista.png'
            with opener.open(url,timeout=10) as response:
                assert response.headers['Content-Type'].startswith('image/png')
                png = response.read()
            with Image.open(io.BytesIO(png)) as preview:
                assert preview.size==(320,240)
                assert preview.convert('L').tobytes()==pixels, 'La vista no corresponde al archivo'
            (study/'vistas'/(Path(label).stem+'-'+mode+'.png')).write_bytes(png)
            result = dict(archivo=label,modo=mode,trabajo=metrics['trabajo'],sesion=receipt['sesion'],
                          nombre_rx=name,sha256_archivo_rx=digest,sha256_original=expected[label],
                          validacion_rx=True,vista_http_verificada=True,recepcion=receipt)
            print('RX_VERIFICADO',label,mode,receipt['sesion'],flush=True)
        except Exception as exc:
            result=dict(registro=record.name,validacion_rx=False,error=str(exc))
            print('ERROR_RX',record.name,str(exc),flush=True)
        results.append(result)
        (study/'validaciones-rx.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
    time.sleep(1)
(study/'validaciones-rx.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
(study/'alimentacion-rx.json').write_text(json.dumps(power_samples,indent=2))
print('RESUMEN_RX',json.dumps(dict(recepciones=len(results),
    validas=sum(x.get('validacion_rx',False) for x in results),
    muestras_alimentacion=len(power_samples),
    alertas_baja_tension=sum(x['baja_tension_activa'] for x in power_samples),
    alertas_limitacion=sum(x['limitacion_activa'] for x in power_samples))),flush=True)

