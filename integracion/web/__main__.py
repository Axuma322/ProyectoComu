"""Servidor WSGI local; no cambia red ni inicia radio/GPIO."""
import argparse

from waitress import serve
from .app import create_app


def main():
    parser = argparse.ArgumentParser(description="Interfaz local ProyectoComu")
    parser.add_argument("--role", choices=["tx", "rx"], required=True)
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--data-dir", help="Directorio local de imágenes y selección")
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("El puerto debe estar entre 1 y 65535")
    app = create_app(args.role, args.data_dir)
    print(f"ProyectoComu {args.role.upper()} · puerto {args.port} · radio e imágenes no integrados", flush=True)
    serve(app, host=args.host, port=args.port, threads=2,
          max_request_body_size=app.config["MAX_CONTENT_LENGTH"])


if __name__ == "__main__":
    main()
