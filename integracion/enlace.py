"""Proceso dueño del nRF24 y, opcionalmente, los controles físicos.

TX consume trabajos locales producidos por Flask o el botón. RX reconstruye y
guarda antes de confirmar FIN. Ambas mitades comparten solo el protocolo nRF24;
la documentación del recorrido está en documentacion/arquitectura_software.md.
"""
import fcntl
import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import struct
import subprocess
import sys
import tempfile
import threading
import time

from transmision.archivos import Receiver, send_file, MAX_WIRE
from transmision.codecs import encode, decode, pixels
from transmision.radio import parser, configuration
from integracion.web.trabajos import write_json, read_json, enqueue


def make_wire(data, metadata):
    """Serializa longitud big-endian, JSON y binario dentro del límite de radio."""
    encoded_meta = json.dumps(metadata, allow_nan=False).encode()
    if len(encoded_meta) > 4096 or len(data) + len(encoded_meta) + 4 > MAX_WIRE:
        raise ValueError('El archivo codificado excede el límite del enlace')
    return struct.pack('>I', len(encoded_meta)) + encoded_meta + data


def reconstruct(wire, root, session, elapsed):
    """Valida y publica una recepción real; un fallo impide confirmar éxito.

    elapsed es el intervalo local de recepción antes de este callback. El tiempo
    de reconstrucción/guardado se registra aparte, sin restar relojes de las Pi.
    """
    if len(wire) < 4:
        raise ValueError('Metadatos incompletos')
    length = struct.unpack_from('>I', wire)[0]
    if not 1 <= length <= 4096 or length + 4 >= len(wire):
        raise ValueError('Longitud de metadatos inválida')
    meta = json.loads(wire[4:4 + length])
    data = wire[4 + length:]
    if len(data) != meta['bytes_comprimidos']:
        raise ValueError('Longitud de archivo codificado incorrecta')
    started = time.monotonic()
    restored = decode(data, meta['modo'])
    if hashlib.sha256(restored).hexdigest() != meta['sha256_reconstruida']:
        raise ValueError('La reconstrucción no coincide con la calculada en TX')
    if meta['modo'] == 'sin_perdidas' and hashlib.sha256(restored).hexdigest() != meta['sha256_original']:
        raise ValueError('El archivo sin pérdidas no coincide con el original')
    image = pixels(restored)
    if image.size != (meta['ancho'], meta['alto']):
        raise ValueError('Dimensiones inconsistentes')
    # El nombre lo genera RX; nunca se usa una ruta enviada por TX.
    ext = '.bmp' if restored.startswith(b'BM') else '.pgm'
    name = f'{session:08x}' + ext
    directory = Path(root) / 'recibidas'
    directory.mkdir(exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=directory)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(restored)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, directory / name)
    finally:
        Path(temporary).unlink(missing_ok=True)
    metrics = dict(meta, descompresion_ms=(time.monotonic() - started) * 1000,
                   recepcion_ms=elapsed * 1000, bytes_utiles_recibidos=len(data),
                   tasa_util_rx_bps=len(data) * 8 / elapsed if elapsed else None,
                   sha256_verificado=True, ber=None, origen_calidad='calculada_en_TX')
    result = dict(nombre=name, ancho=image.width, alto=image.height, sesion=f'{session:08x}',
                  metricas=metrics)
    write_json(Path(root) / 'ultima_recepcion.json', result)
    write_json(Path(root) / 'recepciones' / (f'{session:08x}' + '.json'), result)
    return result


class Controls:
    """GPIO opcionales, todos en BCM; pinout en la guía de LED, botón y DIP.

    RX solo crea LED. Los patrones de parpadeo están en integracion/senales.py.
    Habilitar --gpio exige comprobar el montaje.
    """
    def __init__(self, role):
        from gpiozero import LED, Button
        from integracion.senales import Senales
        self.activity, self.mode, self.finished = LED(23), LED(24), LED(25)
        self.button = Button(17, pull_up=True, bounce_time=0.1) if role == 'tx' else None
        self.dips = [Button(p, pull_up=True) for p in (27, 5, 6, 13)] if role == 'tx' else []
        self.senales = Senales(self.activity, self.mode, self.finished)

    def options(self):
        """Lee DIP al pulsar: automático prima; DIP2/3 eligen 2, 4, 6 o 7 bits."""
        d = [int(x.is_pressed) for x in self.dips]
        return dict(modo='automatico' if d[3] else ('con_perdidas' if d[0] else 'sin_perdidas'),
                    bits=(2, 4, 6, 7)[d[1] * 2 + d[2]])

    def show(self, state, mode=None):
        # En TX el azul sigue al DIP mientras espera; ver senales.patron
        self.senales.mostrar(state, mode, self.options() if self.dips else None)

    def close(self):
        self.senales.cerrar()
        for device in [self.activity, self.mode, self.finished, self.button, *self.dips]:
            if device is not None:
                device.close()


def attach_radio_packages():
    """Reutiliza pyRF24 del venv existente sin instalar ni sustituir paquetes."""
    if importlib.util.find_spec('pyrf24'):
        return
    interpreter = Path.home() / 'comu-venv/bin/python'
    result = subprocess.run([str(interpreter), '-c',
                             'import json,site; print(json.dumps(site.getsitepackages()))'],
                            capture_output=True, text=True, check=True, timeout=10)
    # Solo lectura del entorno que ya funciona; no se instala nada en comu-venv.
    sys.path.extend(json.loads(result.stdout))
    importlib.import_module('pyrf24')


def main():
    cli = parser('Enlace real de imágenes nRF24 para ProyectoComu')
    cli.set_defaults(config=Path(__file__).parents[1] / 'transmision/enlace_imagenes.json')
    cli.add_argument('--role', required=True, choices=('tx', 'rx'))
    cli.add_argument('--data-dir', type=Path, default=Path.home() / '.local/share/proyectocomu-web')
    cli.add_argument('--gpio', action='store_true', help='Habilitar botón, DIP y LED del montaje confirmado')
    cli.add_argument('--check', action='store_true', help='Comprobar dependencias sin abrir SPI ni GPIO')
    args = cli.parse_args()
    config = configuration(args)
    root = args.data_dir.resolve()
    root.mkdir(parents=True, exist_ok=True)
    attach_radio_packages()
    import numpy  # Validar los dos códecs antes de anunciar disponibilidad.
    if args.check:
        print(json.dumps(dict(rol=args.role, configuracion=config, numpy=numpy.__version__)))
        return
    lock_path = Path(tempfile.gettempdir()) / f'proyectocomu-radio-spi0-{config["csn"]}.lock'
    # Un propietario por SPI/CSN. Las pruebas antiguas no comparten este bloqueo,
    # por eso también se revisan sus comandos antes de abrir el hardware.
    lock_fd = os.open(lock_path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    lock = os.fdopen(lock_fd, 'a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit() or int(proc.name) == os.getpid():
            continue
        try:
            command = (proc / 'cmdline').read_bytes().decode(errors='replace').split('\0')
            if any(x.endswith('/prueba_radio.py') or x == 'prueba_radio.py' or
                   x in {'transmision.transmisor.enviar', 'transmision.receptor.escuchar'} for x in command):
                raise RuntimeError('Detén la prueba de radio anterior antes de iniciar el enlace de imágenes')
            if args.gpio and any(x.endswith('/hw_test.py') or x == 'hw_test.py' for x in command):
                raise RuntimeError('Detén hw_test.py antes de habilitar los controles físicos del enlace')
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
    from transmision.enlace import RadioEndpoint
    endpoint = controls = None
    state = dict(rol=args.role, estado='iniciando_radio', progreso=0, error=None)
    last_write = 0
    state_lock = threading.RLock()
    heartbeat_stop = threading.Event()
    heartbeat_thread = None

    def publish(phase=None, **values):
        """Publica estado atómico; RLock coordina worker y hilo de heartbeat."""
        nonlocal last_write
        with state_lock:
            if phase:
                state['estado'] = phase
            if controls and controls.dips:
                # La web ya no elige modo: muestra lo que marcan los switches
                values['dip'] = controls.options()
            state.update(values, heartbeat=time.time())
            write_json(root / 'enlace.json', state)
            last_write = time.monotonic()
            if controls:
                controls.show(state['estado'], state.get('modo'))

    def heartbeat():
        # Huffman puede tardar varios segundos en ARMv6. La disponibilidad del
        # proceso no debe depender de que termine la codificación o un ACK.
        while not heartbeat_stop.wait(1):
            publish()

    def progress(done, total, error=None):
        if time.monotonic() - last_write > 0.4 or error:
            publish('error' if error else ('enviando' if args.role == 'tx' else 'recibiendo'),
                    progreso=round(done * 100 / total, 1), error=error)

    def completed(wire, session, elapsed):
        # Receiver envía el ACK de FIN solo cuando este callback regresa bien.
        result = reconstruct(wire, root, session, elapsed)
        # modo para el LED azul de RX
        publish('completado', progreso=100, sesion=result['sesion'], error=None,
                modo=result['metricas']['modo'])

    try:
        endpoint = RadioEndpoint(config)
        controls = Controls(args.role) if args.gpio else None
        if args.role == 'tx':
            # Recuperar solicitudes interrumpidas: nunca reemitir automáticamente tras reiniciar.
            queue = root / 'cola'
            queue.mkdir(exist_ok=True)
            for old in queue.glob('*.json'):
                old.rename(old.with_suffix('.interrumpido'))
            (root / 'ocupado').unlink(missing_ok=True)
            if controls:
                def press():
                    # Imagen de la selección web; opciones DIP solo para este
                    # trabajo. No sobrescribir preferencias guardadas del teléfono.
                    selected = read_json(root / 'seleccion.json')
                    if not selected:
                        controls.senales.aviso()  # no hay imagen elegida en la web
                        return
                    try:
                        enqueue(root, dict(selected, **controls.options()))
                    except RuntimeError:
                        controls.senales.aviso()  # ya hay un envío en curso
                controls.button.when_pressed = press
        receiver = Receiver(completed, progress)
        publish('esperando' if args.role == 'tx' else 'escuchando', gpio=args.gpio)
        heartbeat_thread = threading.Thread(target=heartbeat, name='comu-heartbeat', daemon=True)
        heartbeat_thread.start()
        while True:
            if args.role == 'rx':
                raw = endpoint.receive(0.1)
                receiver.expire()
                if raw is not None:
                    response = receiver.handle(raw)
                    if response is not None:
                        # Dar margen al TX ARMv6 para terminar write() y volver
                        # a escucha. Una respuesta anticipada puede perderse
                        # aunque el fragmento sí haya obtenido ACK hardware.
                        time.sleep(0.003)
                        endpoint.send(response)
            else:
                jobs = sorted((root / 'cola').glob('*.json'))
                if jobs:
                    jobfile = jobs[0]
                    job = read_json(jobfile)
                    started = time.monotonic()
                    meta, diagnostics = {}, {}
                    counters = (endpoint.frames, endpoint.hardware_retries)
                    try:
                        if not isinstance(job, dict) or Path(job['imagen']).name != job['imagen']:
                            raise ValueError('Solicitud inválida')
                        publish('codificando', progreso=0, error=None, metricas=None, trabajo=job['id'])
                        image_path = root / 'imagenes' / job['imagen']
                        if image_path.is_symlink():
                            raise ValueError('Ruta de imagen inválida')
                        data, meta = encode(image_path, job['modo'], job.get('bits', 4))
                        meta['trabajo'] = job['id']
                        publish('enviando', modo=meta['modo'], metricas=meta)
                        result = send_file(endpoint, make_wire(data, meta), progress,
                                           diagnostics=diagnostics)
                        # Se mide el tiempo total sin imponer el antiguo corte
                        # global. Los plazos por trama siguen dentro de send_file.
                        result.update(meta, total_tx_ms=(time.monotonic() - started) * 1000,
                                      reintentos_hardware=endpoint.hardware_retries - counters[1],
                                      diagnostico=dict(diagnostics))
                        publish('completado', progreso=100, metricas=result, error=None)
                        write_json(root / 'resultados' / (job['id'] + '.json'), result)
                    except Exception as exc:
                        result = dict(meta, confirmado_por_rx=False, error=str(exc),
                                      total_tx_ms=(time.monotonic() - started) * 1000,
                                      reintentos_hardware=endpoint.hardware_retries - counters[1],
                                      diagnostico=dict(diagnostics))
                        publish('error', error=str(exc), metricas=result)
                        if isinstance(job, dict) and 'id' in job:
                            write_json(root / 'resultados' / (job['id'] + '.json'), result)
                            print(json.dumps(dict(evento='envio_fallido', **result)), flush=True)
                    finally:
                        # Liberar la cola también ante fallo; el diagnóstico ya
                        # queda guardado y repetir requiere una nueva solicitud.
                        jobfile.unlink(missing_ok=True)
                        (root / 'ocupado').unlink(missing_ok=True)
                time.sleep(0.02)
            if time.monotonic() - last_write > 1:
                publish()
    except KeyboardInterrupt:
        publish('detenido')
    except Exception as exc:
        publish('error_radio', error=str(exc))
        raise
    finally:
        heartbeat_stop.set()
        if heartbeat_thread:
            heartbeat_thread.join(timeout=3)
        if endpoint:
            endpoint.close()
        if controls:
            controls.close()
        lock.close()


if __name__ == '__main__':
    def stop(*_):
        raise KeyboardInterrupt()
    signal.signal(signal.SIGTERM, stop)
    main()
