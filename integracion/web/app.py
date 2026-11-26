"""Selección local de imágenes. Transporte y códecs pendientes de integración."""
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

MAX_FILE_BYTES = 2 * 1024 * 1024
MODES = {"sin_perdidas", "con_perdidas"}


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
    selection_path = root / "seleccion.json"
    lock = threading.RLock()
    token = secrets.token_urlsafe(32)

    def image_path(name):
        if not isinstance(name, str) or not name or Path(name).name != name or "\\" in name:
            raise ValueError("Nombre de imagen inválido.")
        path = image_dir / name
        if path.is_symlink() or path.resolve().parent != image_dir or not path.is_file():
            raise ValueError("La imagen no existe en el almacenamiento local.")
        return path

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

    def selection():
        try:
            value = json.loads(selection_path.read_text(encoding="utf-8"))
            if value["modo"] not in MODES:
                return None
            details = inspect_image(image_path(value["imagen"]))
            return {"imagen": details["nombre"], "etiqueta": details["etiqueta"], "modo": value["modo"]}
        except (OSError, ValueError, TypeError, KeyError):
            return None

    @app.before_request
    def protect_local_changes():
        if request.method == "POST":
            if role != "tx":
                abort(405, description="El receptor no acepta cargas ni órdenes de transmisión.")
            supplied = request.headers.get("X-Comu-Token", "")
            if not secrets.compare_digest(supplied.encode(), token.encode()):
                abort(403, description="Recarga la página antes de modificar la selección.")

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
            return jsonify(rol=role, radio_integrado=False, codificacion_integrada=False,
                           estado="transmision_no_integrada" if role == "tx" else "recepcion_no_integrada",
                           seleccion=selection() if role == "tx" else None,
                           ultima_imagen=None, metricas=None)

    @app.get("/api/imagenes")
    def images():
        return jsonify(imagenes=catalog())

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
        saved = {"imagen": details["nombre"], "modo": value["modo"]}
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
        return jsonify(error="La transferencia de imágenes por nRF24 aún no está integrada. No se inició un envío."), 501

    return app
