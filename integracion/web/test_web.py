"""Pruebas HTTP locales. No sustituyen la validación en Android ni el enlace RF."""
import io
import json
import re
import tempfile
import unittest
from pathlib import Path

from PIL import Image
from .app import create_app, MAX_FILE_BYTES


class WebTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.app = create_app("tx", self.root)
        self.app.testing = True
        self.client = self.app.test_client()
        self.headers = self.token_headers(self.client)

    @staticmethod
    def token_headers(client):
        html = client.get("/").get_data(as_text=True)
        token = re.search(r'name="comu-token" content="([^"]+)"', html).group(1)
        return {"X-Comu-Token": token}

    @staticmethod
    def image_bytes(mode="L", size=(32, 24), fmt="BMP"):
        stream = io.BytesIO()
        Image.new(mode, size).save(stream, format=fmt)
        stream.seek(0)
        return stream

    def upload(self, stream=None, filename="prueba.bmp"):
        return self.client.post("/api/imagenes", headers=self.headers,
                                data={"imagen": (stream or self.image_bytes(), filename)})

    def test_tx_empty_and_transmission_explicitly_unavailable(self):
        state = self.client.get("/api/estado").json
        self.assertFalse(state["radio_integrado"])
        self.assertIsNone(state["metricas"])
        self.assertIsNone(state["seleccion"])
        response = self.client.post("/api/transmitir", headers=self.headers)
        self.assertEqual(response.status_code, 501)
        self.assertFalse(self.client.get("/api/estado").json["radio_integrado"])

    def test_upload_original_preview_and_persistent_selection(self):
        original = self.image_bytes().getvalue()
        result = self.upload(io.BytesIO(original))
        self.assertEqual(result.status_code, 201)
        name = result.json["imagen"]["nombre"]
        self.assertEqual((self.root / "imagenes" / name).read_bytes(), original)
        self.assertEqual(len(self.client.get("/api/imagenes").json["imagenes"]), 1)
        preview = self.client.get(f"/imagenes/{name}/vista.png")
        self.assertEqual(preview.mimetype, "image/png")
        self.assertEqual(Image.open(io.BytesIO(preview.data)).size, (32, 24))
        for mode in ("sin_perdidas", "con_perdidas"):
            response = self.client.post("/api/seleccion", headers=self.headers,
                                        json={"imagen": name, "modo": mode})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(json.loads((self.root / "seleccion.json").read_text())["modo"], mode)
        restarted = create_app("tx", self.root).test_client()
        self.assertEqual(restarted.get("/api/estado").json["seleccion"]["imagen"], name)

    def test_accept_pgm_and_existing_files(self):
        (self.root / "imagenes" / "local.pgm").write_bytes(self.image_bytes(fmt="PPM").getvalue())
        names = [item["nombre"] for item in self.client.get("/api/imagenes").json["imagenes"]]
        self.assertIn("local.pgm", names)
        self.assertEqual(self.upload(self.image_bytes(fmt="PPM"), "otra.pgm").status_code, 201)

    def test_reject_invalid_color_dimensions_format_and_truncated_file(self):
        cases = [
            (io.BytesIO(b"not an image"), "x.bmp"),
            (self.image_bytes("RGB"), "color.bmp"),
            (self.image_bytes(size=(321, 20)), "ancha.bmp"),
            (self.image_bytes(size=(20, 241)), "alta.bmp"),
            (self.image_bytes(fmt="PNG"), "falsa.bmp"),
            (self.image_bytes(), "imagen.html"),
            (io.BytesIO(self.image_bytes().getvalue()[:100]), "cortada.bmp"),
        ]
        for stream, name in cases:
            with self.subTest(name=name):
                self.assertEqual(self.upload(stream, name).status_code, 400)
        self.assertEqual(list((self.root / "imagenes").iterdir()), [])
        self.assertEqual(list(self.root.glob("tmp*")), [])

    def test_request_size_limit(self):
        result = self.client.post("/api/imagenes", headers=self.headers,
                                  data=b"x" * (MAX_FILE_BYTES + 65537),
                                  content_type="multipart/form-data; boundary=limit")
        self.assertEqual(result.status_code, 413)

    def test_invalid_selection_does_not_overwrite_saved_data(self):
        name = self.upload().json["imagen"]["nombre"]
        valid = {"imagen": name, "modo": "sin_perdidas"}
        self.client.post("/api/seleccion", headers=self.headers, json=valid)
        before = (self.root / "seleccion.json").read_bytes()
        for value in ({"imagen": "../secret.bmp", "modo": "sin_perdidas"},
                      {"imagen": name, "modo": "desconocido"}, {"modo": "sin_perdidas"}, []):
            self.assertEqual(self.client.post("/api/seleccion", headers=self.headers, json=value).status_code, 400)
        self.assertEqual((self.root / "seleccion.json").read_bytes(), before)

    def test_mutations_require_page_token_and_names_are_not_client_paths(self):
        self.assertEqual(self.client.post("/api/transmitir").status_code, 403)
        self.assertEqual(self.client.post("/api/transmitir", headers={"X-Comu-Token": "wrong"}).status_code, 403)
        response = self.upload(filename="../../escape.bmp")
        self.assertEqual(response.status_code, 201)
        self.assertNotIn("/", response.json["imagen"]["nombre"])
        self.assertFalse((self.root.parent / "escape.bmp").exists())

    def test_rx_has_no_upload_no_fake_image_no_metrics(self):
        client = create_app("rx", self.root / "rx").test_client()
        self.assertEqual(client.get("/").status_code, 200)
        state = client.get("/api/estado").json
        self.assertEqual(state["estado"], "recepcion_no_integrada")
        self.assertIsNone(state["ultima_imagen"])
        self.assertIsNone(state["metricas"])
        self.assertEqual(client.post("/api/imagenes").status_code, 405)
        self.assertEqual(client.post("/api/transmitir").status_code, 405)
        self.assertEqual(client.get("/imagenes/example.bmp/vista.png").status_code, 404)

    def test_corrupt_saved_selection_is_not_reported_as_valid(self):
        (self.root / "seleccion.json").write_text('{"imagen": "missing.bmp", "modo": "sin_perdidas"}')
        self.assertIsNone(self.client.get("/api/estado").json["seleccion"])

    def test_role_required(self):
        with self.assertRaises(ValueError):
            create_app("invalid", self.root)


if __name__ == "__main__":
    unittest.main()
