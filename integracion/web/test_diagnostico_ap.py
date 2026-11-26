"""Fixtures sintéticos para probar el observador; no son resultados de equipos."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from .diagnostico_ap import journal_event, stations, Recorder, PROFILE_FIELDS, snapshot


class ObserverTests(unittest.TestCase):
    def test_events_are_distinct_and_do_not_expose_messages(self):
        fixtures = (
            ("AP-STA-CONNECTED aa:bb:cc:dd:ee:ff", "estacion_conectada"),
            ("AP-STA-POSSIBLE-PSK-MISMATCH aa:bb:cc:dd:ee:ff", "wpa_posible_desajuste"),
            ("DHCPACK(wlan0) 192.168.50.16 aa:bb:cc:dd:ee:ff", "dhcp_ack"),
            ("AP-STA-DISCONNECTED aa:bb:cc:dd:ee:ff reason=3", "estacion_desconectada"),
            ("AP-DISABLED", "ap_detenido"),
        )
        for message, event in fixtures:
            record = journal_event({"MESSAGE": message + " password=SECRET psk=SECRET",
                                    "__REALTIME_TIMESTAMP": "1795680000000000"})
            self.assertEqual(record["evento"], event)
            self.assertNotIn("SECRET", json.dumps(record))
            self.assertNotIn("MESSAGE", record)
        self.assertIsNone(journal_event({"MESSAGE": "psk=SECRET"}))
        self.assertIsNone(journal_event({"MESSAGE": ["unexpected"]}))
        record = journal_event({"MESSAGE": "AP-ENABLED", "__MONOTONIC_TIMESTAMP": "123456",
                                "SYSLOG_IDENTIFIER": "wpa_supplicant"})
        self.assertEqual(record["monotonic_us"], 123456)
        self.assertEqual(record["fuente"], "wpa_supplicant")

    def test_no_internet_is_not_inferred_from_disconnect(self):
        record = journal_event({"MESSAGE": "AP-STA-DISCONNECTED aa:bb:cc:dd:ee:ff reason=3"})
        self.assertEqual(record["reason"], 3)
        self.assertNotIn("causa", record)
        self.assertNotIn("internet", json.dumps(record))

    def test_interface_transition_and_authorization(self):
        record = journal_event({"MESSAGE": "device (wlan0): state change: activated -> deactivating"})
        self.assertEqual(record["actual"], "deactivating")
        parsed = stations("Station aa:bb:cc:dd:ee:ff (on wlan0)\n\tauthorized: yes\n\tsignal: -45 dBm\n\tconnected time: 30 seconds\n")
        self.assertTrue(parsed[0]["authorized"])
        self.assertEqual(parsed[0]["signal"], -45)

    def test_recorder_never_overwrites(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "new"
            recorder = Recorder(path)
            recorder.write("eventos", {"evento": "test"})
            recorder.close()
            with self.assertRaises(FileExistsError):
                Recorder(path)
            self.assertEqual(json.loads((path / "eventos.jsonl").read_text())["evento"], "test")

    def test_profile_read_does_not_request_secrets(self):
        self.assertFalse(any(field.endswith(".psk") for field in PROFILE_FIELDS))
        self.assertFalse(any("password" in field or "secret" in field for field in PROFILE_FIELDS))

    def test_snapshot_only_reads_commands_and_local_http_status(self):
        calls = []

        def read(args):
            calls.append(args)
            return 0, "[]" if args[0] == "ip" else ""

        with patch("integracion.web.diagnostico_ap.read_command", side_effect=read), \
             patch("integracion.web.diagnostico_ap.urllib.request.build_opener") as opener:
            opener.return_value.open.return_value.__enter__.return_value.status = 200
            result = snapshot("wlan0", 8080)
            self.assertEqual(result["http_local"], 200)
            url = opener.return_value.open.call_args.args[0]
            self.assertEqual(url, "http://127.0.0.1:8080/api/estado")
        self.assertTrue(all(args[0] in {"iw", "ip"} for args in calls))
        self.assertFalse(any("set" in args or "up" in args or "down" in args for args in calls))


if __name__ == "__main__":
    unittest.main()
