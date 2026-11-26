"""Ensayo real por HTTP local y nRF24; no inicia ni configura radios o redes."""
import hashlib, json, re, secrets, subprocess, sys, time, urllib.request
from pathlib import Path

study = Path(sys.argv[1])
root = Path.home()/'.local/share/proyectocomu-web'
base = 'http://127.0.0.1:8080'
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
def get(route):
    with opener.open(base+route, timeout=10) as r: return json.load(r)
with opener.open(base+'/', timeout=10) as r:
    token = re.search(r'name="comu-token" content="([^"]+)"', r.read().decode()).group(1)
def call(route, body=b'', content_type=None):
    headers = {'X-Comu-Token': token}
    if content_type: headers['Content-Type'] = content_type
    request = urllib.request.Request(base+route, data=body, method='POST', headers=headers)
    with opener.open(request, timeout=15) as r: return json.load(r)
def post(route, value=None):
    return call(route, b'' if value is None else json.dumps(value).encode(), 'application/json')
def save(name, value):
    temporary = study/(name+'.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False))
    temporary.replace(study/name)
def power():
    return subprocess.check_output(['vcgencmd','get_throttled'], text=True, timeout=3).strip()
def upload(item):
    source = study/'entradas'/item['archivo']
    raw = source.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == item['sha256']
    for image in get('/api/imagenes')['imagenes']:
        stored = root/'imagenes'/image['nombre']
        if image['etiqueta'] == item['archivo'] and hashlib.sha256(stored.read_bytes()).hexdigest() == item['sha256']:
            return image['nombre']
    boundary = '----ComuEnsayo'+secrets.token_hex(12)
    body = ('--'+boundary+'\r\nContent-Disposition: form-data; name="imagen"; filename="'+item['archivo']+'"\r\nContent-Type: image/bmp\r\n\r\n').encode()+raw+('\r\n--'+boundary+'--\r\n').encode()
    return call('/api/imagenes', body, 'multipart/form-data; boundary='+boundary)['imagen']['nombre']

manifest = json.loads((study/'entradas.json').read_text())
before = get('/api/estado')
assert before['rol'] == 'tx' and before['radio_integrado']
assert before['enlace']['estado'] not in {'codificando','enviando'}
original_selection = before['seleccion']
save('seleccion-anterior.json', original_selection)
results, last_selection = [], None
fatal = None
try:
    for item in manifest:
        item['almacenada_tx'] = upload(item)
    save('entradas.json', manifest)
    for item in manifest:
        for mode in ('sin_perdidas', 'con_perdidas'):
            case = dict(archivo=item['archivo'], modo=mode, bits=4 if mode=='con_perdidas' else None,
                        sha256_entrada=item['sha256'], alimentacion_antes=power())
            results.append(case)
            try:
                idle_end = time.monotonic()+12
                while (root/'ocupado').exists() and time.monotonic()<idle_end: time.sleep(0.2)
                assert not (root/'ocupado').exists(), 'Hay otra transmisión en curso'
                last_selection = dict(imagen=item['almacenada_tx'], modo=mode, bits=4)
                post('/api/seleccion', last_selection)
                accepted = post('/api/transmitir')
                case['trabajo'] = accepted['trabajo']
                print('INICIO', item['archivo'], mode, case['trabajo'], flush=True)
                end = time.monotonic()+80
                last_phase = None
                while time.monotonic()<end:
                    state = get('/api/estado')['enlace']
                    if state.get('trabajo')==case['trabajo']:
                        phase = state['estado']
                        if phase != last_phase:
                            print('FASE', item['archivo'], mode, phase, flush=True)
                            last_phase = phase
                        if phase in {'completado','error'}:
                            metrics = state.get('metricas') or {}
                            case.update(estado=phase, error=state.get('error'), metricas=metrics)
                            exact = metrics.get('sha256_original') == metrics.get('sha256_reconstruida')
                            quality = metrics.get('mse_tx')==0 or (metrics.get('psnr_tx_db') is not None and metrics['psnr_tx_db']>25)
                            case['cumple_tx'] = bool(phase=='completado' and metrics.get('confirmado_por_rx')
                                and metrics.get('sha256_original')==item['sha256']
                                and (metrics.get('ancho'),metrics.get('alto'))==(320,240)
                                and metrics.get('total_tx_ms',float('inf'))<60000
                                and (exact if mode=='sin_perdidas' else quality))
                            print('RESULTADO', json.dumps(dict(archivo=item['archivo'], modo=mode,
                                estado=phase, cumple_tx=case['cumple_tx'], segundos=metrics.get('total_tx_ms',0)/1000,
                                psnr_db=metrics.get('psnr_tx_db'), reintentos_aplicacion=metrics.get('reintentos_aplicacion'),
                                error=state.get('error'))), flush=True)
                            break
                    time.sleep(0.6)
                else:
                    raise TimeoutError('El observador no vio el final en 80 s')
            except Exception as exc:
                case.update(estado='error_observador', error=str(exc), cumple_tx=False)
                print('ERROR_CASO',item['archivo'],mode,str(exc),flush=True)
            case['alimentacion_despues'] = power()
            save('resultados-tx.json', results)
            if case.get('estado')=='error_observador': raise RuntimeError(case['error'])
            time.sleep(0.5 if case.get('estado')=='completado' else 11)
except Exception as exc:
    fatal = str(exc)
    print('ERROR_ENSAYO',fatal,flush=True)
finally:
    try:
        selected = get('/api/estado')['seleccion']
        if original_selection and selected and last_selection and all(selected.get(k)==v for k,v in last_selection.items()):
            post('/api/seleccion',{k:original_selection[k] for k in ('imagen','modo','bits')})
    except Exception as exc:
        print('AVISO_SELECCION',str(exc),flush=True)
    save('resultados-tx.json', results)
    save('tx-terminado.json',dict(casos=len(results),cumplen=sum(bool(x.get('cumple_tx')) for x in results),error=fatal))
    print('RESUMEN_TX',json.dumps(dict(casos=len(results),cumplen=sum(bool(x.get('cumple_tx')) for x in results),error=fatal)),flush=True)

