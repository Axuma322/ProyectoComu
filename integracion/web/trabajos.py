"""Cola y estado locales compartidos por Flask y un único proceso de radio."""
import json
import os
from pathlib import Path
import tempfile
import time
from uuid import uuid4


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(value, stream, ensure_ascii=False, allow_nan=False)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def read_json(path, default=None):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return default


def worker_state(root):
    state = read_json(Path(root) / 'enlace.json', {})
    state['disponible'] = (time.time() - state.get('heartbeat', 0) < 5 and
                           state.get('estado') not in {'detenido', 'error_radio', 'iniciando_radio'})
    if not state['disponible']:
        state['estado'] = 'proceso_radio_detenido'
    return state


def enqueue(root, selection):
    root = Path(root)
    state = worker_state(root)
    if not state['disponible'] or state.get('estado') == 'error_radio':
        raise RuntimeError('El proceso nRF24 no está activo. Inicia integracion.enlace en TX y RX.')
    queue = root / 'cola'
    queue.mkdir(exist_ok=True)
    # O_EXCL arbitra entre HTTP y botón físico, incluso en procesos distintos.
    try:
        fd = os.open(root / 'ocupado', os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise RuntimeError('Hay una transmisión pendiente o en curso') from None
    job = dict(selection, id=uuid4().hex)
    try:
        os.close(fd)
        write_json(queue / (job['id'] + '.json'), job)
    except Exception:
        (root / 'ocupado').unlink(missing_ok=True)
        raise
    return job['id']
