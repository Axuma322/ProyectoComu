"""Interfaz local; el proceso integracion.enlace es el único dueño del radio."""
from concurrent.futures import ThreadPoolExecutor
import io
import json
import os
import re
import secrets
import tempfile
import threading
import warnings
from pathlib import Path
from uuid import uuid4

from flask import Flask, abort, jsonify, render_template, request, send_file
from PIL import Image, UnidentifiedImageError
from werkzeug.exceptions import HTTPException
from werkzeug.utils import secure_filename
from transmision.codecs import encode, decode, validate_options
from .trabajos import read_json, write_json, worker_state, enqueue

MAX_FILE_BYTES = 2 * 1024 * 1024
MODES = {"sin_perdidas", "con_perdidas", "automatico"}


def inspect_image(path):
    """No convierte el original: solo acepta BMP/PGM gris de hasta 320x240."""
    if path.suffix.lower() not in {".bmp", ".pgm"}:
        raise ValueError("Usa un archivo BMP o PGM en escala de grises.")
    if not 0 < path.stat().st_size <= MAX_FILE_BYTES:
        raise ValueError("La imagen debe ocupar como máximo 2 MiB.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(path) as image:
                expected = "BMP" if path.suffix.lower() == ".bmp" else "PPM"
                if image.format != expected:
                    raise ValueError("El contenido no coincide con el formato BMP/PGM.")
                if not (1 <= image.width <= 320 and 1 <= image.height <= 240):
                    raise ValueError("El tamaño máximo es 320 × 240 píxeles.")
                image.load()
                if image.mode not in {"1", "L", "P"}:
                    raise ValueError("La imagen debe estar en escala de grises de hasta 8 bits.")
                if image.mode == "P":
                    # BMP indexado: comprobar los colores utilizados, no solo su modo.
                    rgb = image.convert("RGB")
                    if any(r != g or g != b for r, g, b in rgb.getdata()):
                        raise ValueError("La paleta contiene colores; usa escala de grises.")
                label = re.sub(r"^[0-9a-f]{32}_", "", path.name)
                return {"nombre": path.name, "etiqueta": label, "ancho": image.width,
                        "alto": image.height, "bytes": path.stat().st_size}
    except (UnidentifiedImageError, OSError, SyntaxError,
            Image.DecompressionBombWarning, Image.DecompressionBombError) as exc:
        raise ValueError("No se pudo leer una imagen BMP/PGM válida y completa.") from exc


def create_app(role=None, data_dir=None):
    role = role or os.environ.get("COMU_ROLE")
    if role not in {"tx", "rx"}:
        raise ValueError("Indica el rol tx o rx; no se elige automáticamente.")
    app = Flask(__name__)
    app.config.update(MAX_CONTENT_LENGTH=MAX_FILE_BYTES + 64 * 1024)
    root = Path(data_dir or os.environ.get("COMU_DATA_DIR", "~/.local/share/proyectocomu-web")).expanduser().resolve()
    image_dir = root / "imagenes"
    image_dir.mkdir(parents=True, exist_ok=True)
    received_dir = root / 'recibidas'
    received_dir.mkdir(exist_ok=True)
    selection_path = root / "seleccion.json"
    lock = threading.RLock()
    token = secrets.token_urlsafe(32)
    executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='comu-codec')
    compression = None

    def stored_path(directory, name):
        if not isinstance(name, str) or not name or Path(name).name != name or "\\" in name:
            raise ValueError("Nombre de imagen inválido.")
        path = directory / name
        if path.is_symlink() or path.resolve().parent != directory or not path.is_file():
            raise ValueError("La imagen no existe en el almacenamiento local.")
        return path

    def image_path(name):
        return stored_path(image_dir, name)

    def catalog():
        result = []
        if role == "tx":
            for path in sorted(image_dir.iterdir()):
                if path.is_symlink() or not path.is_file():
                    continue
                try:
                    result.append(inspect_image(path))
                except (ValueError, OSError):
                    continue
        return result

    def received_details(path):
        details = inspect_image(path)
        meta = read_json(root / 'recepciones' / (path.stem + '.json'), {})
        if not meta or meta.get('nombre') != path.name:
            meta = read_json(root / 'ultima_recepcion.json', {})
        if not meta or meta.get('nombre') != path.name:
            meta = {}
        label = meta.get('metricas', {}).get('nombre', path.name)
        return dict(details, etiqueta=re.sub(r'^[0-9a-f]{32}_', '', label),
                    metricas=meta.get('metricas'), sesion=meta.get('sesion', path.stem),
                    guardada_en=path.stat().st_mtime,
                    url='/recibidas/' + path.name + '/vista.png')

    def received_catalog():
        result = []
        if role == 'rx':
            for path in received_dir.iterdir():
                if path.is_symlink() or not path.is_file():
                    continue
                try:
                    result.append(received_details(path))
                except (ValueError, OSError):
                    continue
        return sorted(result, key=lambda item: (item['guardada_en'], item['nombre']), reverse=True)

    def latest_received():
        last = read_json(root / 'ultima_recepcion.json', {})
        if last:
            try:
                return received_details(stored_path(received_dir, last['nombre']))
            except (ValueError, OSError, KeyError):
                pass
        items = received_catalog()
        return items[0] if items else None

    def selection():
        try:
            value = json.loads(selection_path.read_text(encoding="utf-8"))
            if value["modo"] not in MODES:
                return None
            details = inspect_image(image_path(value["imagen"]))
            options = validate_options(value['modo'], value.get('bits', 4))
            return {"imagen": details["nombre"], "etiqueta": details["etiqueta"], **options}
        except (OSError, ValueError, TypeError, KeyError):
            return None

    @app.before_request
    def protect_local_changes():
        if request.method in {"POST", "DELETE"}:
            if request.method == 'POST' and role != "tx":
                abort(405, description="El receptor no acepta cargas ni órdenes de transmisión.")
            supplied = request.headers.get("X-Comu-Token", "")
            if not secrets.compare_digest(supplied.encode(), token.encode()):
                abort(403, description="Recarga la página antes de modificar las imágenes o la selección.")

    @app.after_request
    def local_headers(response):
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; img-src 'self'; script-src 'self'; "
            "style-src 'self'; connect-src 'self'; frame-ancestors 'none'; "
            "base-uri 'none'; form-action 'self'"
        )
        return response

    @app.errorhandler(HTTPException)
    def http_error(exc):
        message = "La carga supera el límite de 2 MiB." if exc.code == 413 else exc.description
        return jsonify(error=message), exc.code

    @app.errorhandler(OSError)
    def storage_error(exc):
        app.logger.exception("Error de almacenamiento local")
        return jsonify(error="No se pudo acceder al almacenamiento de la Raspberry."), 500

    @app.get("/")
    def index():
        return render_template("index.html", role=role, token=token)

    @app.get("/api/estado")
    def status():
        with lock:
            state = worker_state(root)
            last = latest_received() if role == 'rx' else None
            return jsonify(rol=role, radio_integrado=state['disponible'] and state.get('estado') != 'error_radio',
                           codificacion_integrada=True, enlace=state,
                           estado=state['estado'], codificacion=read_json(root / 'codificacion.json'),
                           seleccion=selection() if role == "tx" else None,
                           ultima_imagen=last,
                           metricas=last.get('metricas') if last else state.get('metricas'))

    @app.get("/api/imagenes")
    def images():
        return jsonify(imagenes=catalog())

    @app.get('/api/recibidas')
    def received_images():
        if role != 'rx':
            abort(404)
        return jsonify(imagenes=received_catalog())

    @app.delete('/api/imagenes/<name>')
    def delete_image(name):
        if role != 'tx':
            abort(405)
        with lock:
            try:
                path = image_path(name)
            except ValueError as exc:
                abort(404, description=str(exc))
            if compression is not None and not compression.done():
                abort(409, description='Espera a que termine la compresión local antes de borrar imágenes.')
            try:
                descriptor = os.open(root / 'ocupado', os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            except FileExistsError:
                abort(409, description='Espera a que termine la transmisión antes de borrar imágenes.')
            try:
                os.close(descriptor)
                saved = read_json(selection_path, {})
                path.unlink()
                if saved.get('imagen') == name:
                    selection_path.unlink(missing_ok=True)
                codec = read_json(root / 'codificacion.json', {})
                if codec.get('metricas', {}).get('nombre') == name[-120:]:
                    (root / 'codificacion.json').unlink(missing_ok=True)
                    for artifact in ('archivo.bin', 'reconstruida'):
                        (root / 'codificada' / artifact).unlink(missing_ok=True)
            finally:
                (root / 'ocupado').unlink(missing_ok=True)
        return jsonify(mensaje='Imagen borrada de TX.')

    @app.delete('/api/recibidas/<name>')
    def delete_received_image(name):
        if role != 'rx':
            abort(405)
        with lock:
            try:
                path = stored_path(received_dir, name)
                inspect_image(path)
            except ValueError as exc:
                abort(404, description=str(exc))
            path.unlink()
            (root / 'recepciones' / (path.stem + '.json')).unlink(missing_ok=True)
        return jsonify(mensaje='Imagen borrada de RX.')

    @app.post("/api/imagenes")
    def upload():
        uploaded = request.files.get("imagen")
        if uploaded is None or not uploaded.filename:
            abort(400, description="Selecciona una imagen BMP o PGM.")
        name = secure_filename(uploaded.filename)
        suffix = Path(name).suffix.lower()
        if suffix not in {".bmp", ".pgm"}:
            abort(400, description="Solo se aceptan BMP y PGM.")
        # Archivo temporal: validar antes de publicar; nunca usar la ruta del cliente.
        descriptor, temporary = tempfile.mkstemp(dir=root, suffix=suffix)
        path = Path(temporary)
        try:
            with os.fdopen(descriptor, "wb") as output:
                output.write(uploaded.stream.read(MAX_FILE_BYTES + 1))
            inspect_image(path)
            final = image_dir / (uuid4().hex + "_" + name[-120:])
            path.replace(final)
            return jsonify(imagen=inspect_image(final)), 201
        except ValueError as exc:
            abort(400, description=str(exc))
        finally:
            path.unlink(missing_ok=True)

    @app.post("/api/seleccion")
    def select():
        value = request.get_json(silent=True)
        if not isinstance(value, dict) or value.get("modo") not in MODES:
            abort(400, description="Selecciona modo con pérdidas o sin pérdidas.")
        try:
            details = inspect_image(image_path(value.get("imagen")))
        except ValueError as exc:
            abort(400, description=str(exc))
        try:
            saved = {"imagen": details["nombre"], **validate_options(value['modo'], value.get('bits', 4))}
        except ValueError as exc:
            abort(400, description=str(exc))
        with lock:
            descriptor, temporary = tempfile.mkstemp(dir=root, suffix=".json")
            try:
                with os.fdopen(descriptor, "w", encoding="utf-8") as output:
                    json.dump(saved, output, ensure_ascii=False)
                Path(temporary).replace(selection_path)
            finally:
                Path(temporary).unlink(missing_ok=True)
        return jsonify(seleccion=saved, mensaje="Selección guardada localmente. No se transmitió ningún dato.")

    @app.get("/imagenes/<name>/vista.png")
    def preview(name):
        if role != "tx":
            abort(404, description="Todavía no hay una imagen reconstruida.")
        try:
            path = image_path(name)
            inspect_image(path)
        except ValueError as exc:
            abort(404, description=str(exc))
        buffer = io.BytesIO()
        with Image.open(path) as image:
            image.convert("L").save(buffer, format="PNG")
        buffer.seek(0)
        # PNG es solo vista web: nunca reemplaza el archivo fuente ni cruza nRF24.
        return send_file(buffer, mimetype="image/png")

    @app.post("/api/transmitir")
    def transmit():
        saved = selection()
        if not saved:
            abort(400, description='Primero guarda la imagen y los parámetros de codificación.')
        if not worker_state(root)['disponible']:
            abort(503, description='El proceso nRF24 está detenido. Inicia integracion.enlace en ambas Raspberry.')
        try:
            job = enqueue(root, saved)
        except RuntimeError as exc:
            abort(409, description=str(exc))
        return jsonify(trabajo=job, mensaje='Solicitud aceptada por TX; espera la confirmación real de RX.'), 202

    @app.post('/api/codificar')
    def compress_local():
        nonlocal compression
        selected = selection()
        if not selected:
            abort(400, description='Primero guarda una selección válida.')
        with lock:
            if compression is not None and not compression.done():
                abort(409, description='Ya hay una codificación local en curso.')
            path = image_path(selected['imagen'])
            write_json(root / 'codificacion.json', {'estado': 'codificando'})

            def work():
                try:
                    data, meta = encode(path, selected['modo'], selected['bits'])
                    directory = root / 'codificada'
                    directory.mkdir(exist_ok=True)
                    (directory / 'archivo.bin').write_bytes(data)
                    (directory / 'reconstruida').write_bytes(decode(data, meta['modo']))
                    write_json(root / 'codificacion.json', dict(estado='completado', metricas=meta,
                               vista='/codificada/vista.png', descarga='/codificada/archivo.bin'))
                except Exception as exc:
                    write_json(root / 'codificacion.json', dict(estado='error', error=str(exc)))
            compression = executor.submit(work)
        return jsonify(mensaje='Codificación local iniciada en TX. No se transmitió por radio.'), 202

    @app.get('/codificada/archivo.bin')
    def download_encoded():
        if role != 'tx' or read_json(root / 'codificacion.json', {}).get('estado') != 'completado':
            abort(404)
        return send_file(root / 'codificada/archivo.bin', as_attachment=True, download_name='imagen-codificada.bin')

    @app.get('/codificada/vista.png')
    def encoded_preview():
        if role != 'tx' or read_json(root / 'codificacion.json', {}).get('estado') != 'completado':
            abort(404)
        return png(root / 'codificada/reconstruida')

    def png(path):
        buffer = io.BytesIO()
        with Image.open(path) as image:
            image.convert('L').save(buffer, format='PNG')
        buffer.seek(0)
        return send_file(buffer, mimetype='image/png')

    @app.get('/recibidas/<name>/vista.png')
    def received_preview(name):
        if role != 'rx':
            abort(404)
        try:
            path = stored_path(received_dir, name)
            inspect_image(path)
        except ValueError:
            abort(404)
        return png(path)

    return app
