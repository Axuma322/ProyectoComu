"""Pruebas HTTP locales. No sustituyen la validación en Android ni el enlace RF."""
import io
import json
import re
import tempfile
import unittest
import time
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

    def test_tx_empty_and_web_cannot_transmit(self):
        state = self.client.get("/api/estado").json
        self.assertFalse(state["radio_integrado"])
        self.assertIsNone(state["metricas"])
        self.assertIsNone(state["seleccion"])
        # Solo el botón físico transmite
        response = self.client.post("/api/transmitir", headers=self.headers)
        self.assertEqual(response.status_code, 403)
        self.assertTrue(state['codificacion_integrada'])
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
        self.assertEqual(state["estado"], "proceso_radio_detenido")
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

    def test_local_codec_uses_dip_and_preserves_original(self):
        from .trabajos import write_json
        name = self.upload().json['imagen']['nombre']
        self.client.post('/api/seleccion', headers=self.headers, json=dict(imagen=name))
        # Sin lectura de switches no hay modo que probar
        self.assertEqual(self.client.post('/api/codificar', headers=self.headers).status_code, 409)
        for mode in ('sin_perdidas', 'con_perdidas'):
            original = (self.root / 'imagenes' / name).read_bytes()
            write_json(self.root / 'enlace.json', dict(heartbeat=time.time(), estado='esperando',
                                                       dip=dict(modo=mode, bits=4)))
            self.assertEqual(self.client.post('/api/codificar', headers=self.headers).status_code, 202)
            end = time.monotonic() + 15
            while time.monotonic() < end:
                state = self.client.get('/api/estado').json['codificacion']
                if state['estado'] != 'codificando':
                    break
                time.sleep(0.05)
            self.assertEqual(state['estado'], 'completado', state)
            self.assertEqual(state['metricas']['modo'], mode)
            if mode == 'con_perdidas':
                self.assertEqual(state['metricas']['bits'], 4)
            self.assertEqual(self.client.get(state['vista']).mimetype, 'image/png')
            download = self.client.get(state['descarga'])
            self.assertEqual(download.status_code, 200)
            download.close()
            self.assertEqual((self.root / 'imagenes' / name).read_bytes(), original)

    def test_quality_validation_and_button_queue(self):
        from .trabajos import write_json, enqueue
        name = self.upload().json['imagen']['nombre']
        for bits in (0, 8, True, '4', 4.5):
            self.assertEqual(self.client.post('/api/seleccion', headers=self.headers,
                             json=dict(imagen=name, modo='con_perdidas', bits=bits)).status_code, 400)
        # El teléfono solo manda la imagen
        self.assertEqual(self.client.post('/api/seleccion', headers=self.headers,
                                          json=dict(imagen=name)).status_code, 200)
        self.assertEqual(self.client.post('/api/transmitir', headers=self.headers).status_code, 403)
        # Así encola el botón: imagen guardada + lo que diga el DIP
        selected = json.loads((self.root / 'seleccion.json').read_text())
        with self.assertRaises(RuntimeError):
            enqueue(self.root, dict(selected, modo='con_perdidas', bits=6))
        # Heartbeat de prueba local: no es una transmisión RF.
        write_json(self.root / 'enlace.json', dict(heartbeat=time.time(), estado='esperando'))
        job_id = enqueue(self.root, dict(selected, modo='con_perdidas', bits=6))
        job = json.loads((self.root / 'cola' / (job_id + '.json')).read_text())
        self.assertEqual((job['imagen'], job['bits']), (name, 6))
        with self.assertRaises(RuntimeError):
            enqueue(self.root, dict(selected, modo='con_perdidas', bits=6))

    def test_delete_tx_clears_selection_and_derived_files_but_keeps_other_images(self):
        name = self.upload().json['imagen']['nombre']
        other = self.upload(filename='conservar.bmp').json['imagen']['nombre']
        self.client.post('/api/seleccion', headers=self.headers,
                         json=dict(imagen=name, modo='sin_perdidas'))
        from .trabajos import write_json
        write_json(self.root / 'codificacion.json', dict(estado='completado', metricas=dict(nombre=name)))
        (self.root / 'codificada').mkdir()
        for artifact in ('archivo.bin', 'reconstruida'):
            (self.root / 'codificada' / artifact).write_bytes(b'artefacto de prueba')
        self.assertEqual(self.client.delete('/api/imagenes/' + name, headers=self.headers).status_code, 200)
        self.assertFalse((self.root / 'imagenes' / name).exists())
        self.assertTrue((self.root / 'imagenes' / other).exists())
        self.assertIsNone(self.client.get('/api/estado').json['seleccion'])
        self.assertIsNone(self.client.get('/api/estado').json['codificacion'])
        self.assertEqual(list((self.root / 'codificada').iterdir()), [])
        restarted = create_app('tx', self.root).test_client()
        self.assertEqual([x['nombre'] for x in restarted.get('/api/imagenes').json['imagenes']], [other])

    def test_delete_is_protected_and_cannot_remove_inflight_or_external_image(self):
        name = self.upload().json['imagen']['nombre']
        url = '/api/imagenes/' + name
        self.assertEqual(self.client.delete(url).status_code, 403)
        (self.root / 'ocupado').touch()
        self.assertEqual(self.client.delete(url, headers=self.headers).status_code, 409)
        self.assertTrue((self.root / 'imagenes' / name).exists())
        (self.root / 'ocupado').unlink()
        outside = self.root / 'conservar.bmp'
        outside.write_bytes(self.image_bytes().getvalue())
        (self.root / 'imagenes' / 'enlace.bmp').symlink_to(outside)
        self.assertEqual(self.client.delete('/api/imagenes/enlace.bmp', headers=self.headers).status_code, 404)
        self.assertEqual(self.client.delete('/api/imagenes/..%5Cconservar.bmp', headers=self.headers).status_code, 404)
        self.assertTrue(outside.exists())

    def test_rx_gallery_preserves_per_image_metrics_and_deletes_latest_then_all(self):
        from integracion.enlace import make_wire, reconstruct
        from transmision.codecs import encode
        rxroot = self.root / 'rx'
        client = create_app('rx', rxroot).test_client()
        headers = self.token_headers(client)
        source = self.root / 'fuente.bmp'
        source.write_bytes(self.image_bytes().getvalue())
        first = None
        for session, mode in ((1, 'sin_perdidas'), (2, 'con_perdidas')):
            data, meta = encode(source, mode, 4)
            result = reconstruct(make_wire(data, meta), rxroot, session, 0.25)
            if first is None:
                first = result['nombre']
        latest = result['nombre']
        gallery = client.get('/api/recibidas').json['imagenes']
        self.assertEqual(len(gallery), 2)
        self.assertEqual({x['metricas']['modo'] for x in gallery}, {'sin_perdidas', 'con_perdidas'})
        self.assertEqual(client.get('/recibidas/' + first + '/vista.png').status_code, 200)
        self.assertEqual(client.get('/api/estado').json['ultima_imagen']['nombre'], latest)
        self.assertEqual(client.delete('/api/recibidas/' + latest).status_code, 403)
        self.assertEqual(client.delete('/api/recibidas/' + latest, headers=headers).status_code, 200)
        self.assertFalse((rxroot / 'recepciones/00000002.json').exists())
        state = client.get('/api/estado').json
        self.assertEqual(state['ultima_imagen']['nombre'], first)
        self.assertEqual(state['metricas']['modo'], 'sin_perdidas')
        self.assertEqual(client.get('/recibidas/' + latest + '/vista.png').status_code, 404)
        restarted = create_app('rx', rxroot).test_client()
        self.assertEqual(len(restarted.get('/api/recibidas').json['imagenes']), 1)
        self.assertEqual(client.delete('/api/recibidas/' + first, headers=headers).status_code, 200)
        state = client.get('/api/estado').json
        self.assertIsNone(state['ultima_imagen'])
        self.assertIsNone(state['metricas'])

    def test_rx_gallery_lists_legacy_image_without_inventing_metrics(self):
        rxroot = self.root / 'rx'
        client = create_app('rx', rxroot).test_client()
        (rxroot / 'recibidas/antigua.bmp').write_bytes(self.image_bytes().getvalue())
        gallery = client.get('/api/recibidas').json['imagenes']
        self.assertEqual(len(gallery), 1)
        self.assertIsNone(gallery[0]['metricas'])
        self.assertEqual(client.get(gallery[0]['url']).status_code, 200)
        headers = self.token_headers(client)
        self.assertEqual(client.delete('/api/imagenes/antigua.bmp', headers=headers).status_code, 405)


if __name__ == "__main__":
    unittest.main()
