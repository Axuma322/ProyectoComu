"""Observador Linux de solo lectura. No activa AP, radio ni cambia servicios.

Guarda eventos estructurados, no mensajes completos del journal ni claves WPA.
Usa solo la biblioteca estándar; no necesita el entorno del radio o Flask.
"""
import argparse
from datetime import datetime, timezone
import ipaddress
import json
import os
from pathlib import Path
import re
import subprocess
import threading
import time
import urllib.error
import urllib.request

PROFILE_FIELDS = (
    "connection.id", "connection.uuid", "connection.autoconnect",
    "802-11-wireless.ssid", "802-11-wireless.mode", "802-11-wireless.band",
    "802-11-wireless.channel", "802-11-wireless-security.key-mgmt",
    "802-11-wireless-security.proto", "802-11-wireless-security.pairwise",
    "802-11-wireless-security.group", "802-11-wireless-security.pmf",
    "ipv4.method", "ipv4.addresses", "ipv4.never-default", "ipv6.method",
)
JOURNAL_MATCH = [
    "_SYSTEMD_UNIT=NetworkManager.service", "+",
    "_SYSTEMD_UNIT=wpa_supplicant.service", "+",
    "SYSLOG_IDENTIFIER=NetworkManager", "+", "SYSLOG_IDENTIFIER=wpa_supplicant", "+",
    "SYSLOG_IDENTIFIER=dnsmasq", "+", "SYSLOG_IDENTIFIER=dnsmasq-dhcp", "+",
    "_TRANSPORT=kernel",
]
MAC = re.compile(r"\b(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}\b")
EVENTS = (
    (r"AP-STA-POSSIBLE-PSK-MISMATCH", "wpa_posible_desajuste"),
    (r"AP-STA-DISCONNECTED", "estacion_desconectada"),
    (r"AP-STA-CONNECTED", "estacion_conectada"),
    (r"AP-ENABLED|Started Wi-Fi Hotspot", "ap_iniciado"),
    (r"AP-DISABLED|Stopped Wi-Fi Hotspot", "ap_detenido"),
    (r"pairwise key handshake completed|Key negotiation completed", "wpa_completado"),
    (r"(?:4-Way Handshake|4-way handshake).*(?:fail|timeout)|EAPOL.*timeout", "wpa_fallo_o_timeout"),
    (r"CTRL-EVENT-DISCONNECTED|\bdeauthenticated\b|\bdisassociated\b", "desconexion_80211"),
    (r"\bDHCPDISCOVER\b", "dhcp_discover"),
    (r"\bDHCPOFFER\b", "dhcp_offer"),
    (r"\bDHCPREQUEST\b", "dhcp_request"),
    (r"\bDHCPACK\b", "dhcp_ack"),
    (r"\bDHCPNAK\b", "dhcp_nak"),
    (r"\bDHCPDECLINE\b", "dhcp_decline"),
    (r"brcmfmac.*(?:error|fail|timeout|timed out|reset)", "aviso_controlador"),
    (r"under.?voltage", "aviso_alimentacion"),
)


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def journal_event(entry):
    """Extrae únicamente tipos, MAC/IP y códigos; nunca vuelca MESSAGE."""
    message = entry.get("MESSAGE")
    if not isinstance(message, str):
        return None
    event = next((name for pattern, name in EVENTS if re.search(pattern, message, re.I)), None)
    state = re.search(r"device \(([A-Za-z0-9_.:-]{1,32})\): state change: ([a-z-]+) -> ([a-z-]+)", message)
    if event is None and state is None:
        return None
    record = {"evento": event or "estado_interfaz"}
    timestamp = str(entry.get("__REALTIME_TIMESTAMP", ""))
    if timestamp.isdigit():
        record["fecha_utc"] = datetime.fromtimestamp(int(timestamp) / 1e6, timezone.utc).isoformat()
    monotonic = str(entry.get("__MONOTONIC_TIMESTAMP", ""))
    if monotonic.isdigit():
        record["monotonic_us"] = int(monotonic)
    source = entry.get("SYSLOG_IDENTIFIER")
    if source in {"NetworkManager", "wpa_supplicant", "dnsmasq", "dnsmasq-dhcp", "kernel"}:
        record["fuente"] = source
    if state:
        record.update(interfaz=state[1][:32], anterior=state[2], actual=state[3])
    record["mac"] = sorted(set(value.lower() for value in MAC.findall(message)))
    addresses = []
    for value in re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", message):
        try:
            addresses.append(str(ipaddress.IPv4Address(value)))
        except ValueError:
            pass
    record["ipv4"] = sorted(set(addresses))
    reason = re.search(r"\breason[= ](\d+)\b", message)
    if reason:
        record["reason"] = int(reason[1])
    return record


def read_command(args):
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=5, check=False)
        return result.returncode, result.stdout
    except FileNotFoundError:
        return 127, ""
    except subprocess.TimeoutExpired:
        return 124, ""
    except OSError:
        return 126, ""


def stations(text):
    result = []
    current = None
    for line in text.splitlines():
        match = re.match(r"Station ([0-9a-fA-F:]{17})", line)
        if match:
            current = {"mac": match[1].lower()}
            result.append(current)
        elif current is not None:
            match = re.match(r"\s*(authorized|authenticated|associated):\s*(yes|no)\b", line)
            if match:
                current[match[1]] = match[2] == "yes"
            match = re.match(r"\s*(signal|connected time|inactive time):\s*(-?\d+)", line)
            if match:
                current[match[1]] = int(match[2])
    return result


def snapshot(interface, port):
    record = {"fecha_utc": utc_now(), "monotonic_us": int(time.monotonic() * 1e6)}
    code, text = read_command(["iw", "dev", interface, "info"])
    record["iw_info_codigo"] = code
    for key, pattern in (("tipo", r"\btype (\w+)"), ("canal", r"\bchannel (\d+)"),
                         ("ancho_mhz", r"\bwidth: (\d+) MHz")):
        match = re.search(pattern, text)
        if match:
            record[key] = match[1]
    code, text = read_command(["iw", "dev", interface, "station", "dump"])
    record.update(estaciones_codigo=code, estaciones=stations(text))
    for category, command in (("direcciones", ["ip", "-j", "-4", "address", "show", "dev", interface]),
                              ("vecinos", ["ip", "-j", "-4", "neigh", "show", "dev", interface])):
        code, text = read_command(command)
        record[category + "_codigo"] = code
        try:
            values = json.loads(text) if code == 0 else []
            if category == "direcciones":
                record[category] = [{k: item[k] for k in ("local", "prefixlen") if k in item}
                                    for device in values for item in device.get("addr_info", [])]
            else:
                record[category] = [{k: item[k] for k in ("dst", "lladdr", "state") if k in item}
                                    for item in values]
        except (ValueError, TypeError, KeyError):
            record[category] = []
    # Consulta solo HTTP local y no guarda el cuerpo ni lo interpreta como estado RF.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(f"http://127.0.0.1:{port}/api/estado", timeout=2) as response:
            record["http_local"] = response.status
    except urllib.error.HTTPError as exc:
        record["http_local"] = exc.code
    except (OSError, urllib.error.URLError):
        record["http_local"] = None
    return record


class Recorder:
    def __init__(self, directory):
        directory.mkdir(mode=0o700, parents=True, exist_ok=False)
        self.files = {}
        self.lock = threading.Lock()
        for kind in ("eventos", "estado"):
            descriptor = os.open(directory / (kind + ".jsonl"), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            self.files[kind] = os.fdopen(descriptor, "w", encoding="utf-8")

    def write(self, kind, record):
        with self.lock:
            self.files[kind].write(json.dumps(record, ensure_ascii=False) + "\n")
            self.files[kind].flush()

    def close(self):
        for output in self.files.values():
            output.close()


def history(recorder, minutes):
    code, text = read_command(["journalctl", "--boot", "--no-pager", "--output=json",
                               "--since", f"{minutes} minutes ago", "--lines=5000"] + JOURNAL_MATCH)
    recorder.write("estado", {"fecha_utc": utc_now(), "journal_historial_codigo": code})
    for line in text.splitlines():
        try:
            entry = journal_event(json.loads(line))
        except (ValueError, TypeError, OverflowError):
            continue
        if entry:
            recorder.write("eventos", entry)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interface", default="wlan0")
    parser.add_argument("--profile", default="Comu-TX")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--output", type=Path, required=True, help="Directorio nuevo; nunca se sobrescribe")
    parser.add_argument("--history-minutes", type=int, default=60)
    parser.add_argument("--duration", type=int, default=0, help="Segundos de observación; 0 = solo historial y una lectura")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_.:-]+", args.interface) or args.interface.startswith("-"):
        parser.error("Interfaz inválida")
    if not 1 <= args.port <= 65535 or not 0 <= args.duration <= 7200 or not 1 <= args.history_minutes <= 1440:
        parser.error("Puerto/tiempos fuera de rango")
    recorder = Recorder(args.output)
    process = None
    thread = None
    try:
        code, text = read_command(["nmcli", "-g", ",".join(PROFILE_FIELDS), "connection", "show", "id", args.profile])
        values = text.splitlines() if code == 0 else []
        recorder.write("estado", {"fecha_utc": utc_now(), "perfil_codigo": code,
                                  "perfil": dict(zip(PROFILE_FIELDS, values))})
        history(recorder, args.history_minutes)
        if args.duration:
            # Seguir desde ahora antes de leer estaciones evita perder intentos durante la lectura.
            process = subprocess.Popen(["journalctl", "--boot", "--follow", "--lines=0", "--output=json"] + JOURNAL_MATCH,
                                       stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)

            def follow():
                for line in process.stdout:
                    try:
                        record = journal_event(json.loads(line))
                    except (ValueError, TypeError, OverflowError):
                        continue
                    if record:
                        recorder.write("eventos", record)

            thread = threading.Thread(target=follow, daemon=True)
            thread.start()
        print(f"Observación de solo lectura en {args.output}", flush=True)
        deadline = time.monotonic() + args.duration
        while True:
            recorder.write("estado", snapshot(args.interface, args.port))
            if process is not None and process.poll() is not None:
                recorder.write("estado", {"fecha_utc": utc_now(), "journal_seguimiento_codigo": process.returncode})
                break
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            time.sleep(min(5, remaining))
    except KeyboardInterrupt:
        pass
    finally:
        if process is not None:
            if process.poll() is None:
                process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        if thread is not None:
            thread.join(timeout=5)
        if process is not None:
            process.stdout.close()
        recorder.close()


if __name__ == "__main__":
    main()
