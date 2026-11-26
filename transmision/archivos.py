"""Transferencias binarias de 32 bytes, stop-and-wait y confirmación de aplicación.

El endpoint real está en enlace.py. Los endpoints de pruebas no se usan en producción.
"""
import math
import secrets
import struct
import time
import zlib

HEADER = struct.Struct('>BBIH')
MAGIC = 0xC1
START, DATA, FIN, ACK = 1, 2, 3, 4
CHUNK = 24
MAX_WIRE = 256 * 1024


def packet(kind, session, index=0, body=b''):
    """Construye 32 bytes; el receptor recorta el relleno con la longitud START."""
    if len(body) > CHUNK:
        raise ValueError('Fragmento demasiado grande')
    return HEADER.pack(MAGIC, kind, session, index) + body.ljust(CHUNK, b'\0')


def unpack(raw):
    """Rechaza longitud, identificador de formato o tipo ajenos al protocolo."""
    if len(raw) != 32:
        raise ValueError('Trama incompleta')
    magic, kind, session, index = HEADER.unpack_from(raw)
    if magic != MAGIC or kind not in (START, DATA, FIN, ACK):
        raise ValueError('Versión o tipo de trama desconocido')
    return kind, session, index, raw[HEADER.size:]


class Receiver:
    """Reensambla una sesión activa y reconoce cierres repetidos durante 90 s.

    complete recibe el flujo completo, sesión e intervalo local. Debe validar y
    guardar antes de volver: de eso depende el estado del ACK final.
    """
    def __init__(self, complete, progress=lambda *_: None):
        self.complete, self.progress = complete, progress
        self.current = None
        self.closed = {}

    def expire(self):
        """Caduca por silencio de TX, no por duración total de la transferencia."""
        if self.current and time.monotonic() - self.current['seen'] > 10:
            self.progress(0, self.current['size'], 'Recepción incompleta: TX dejó de enviar fragmentos')
            self.current = None

    def handle(self, raw):
        """Devuelve ACK de aplicación o None; un duplicado no duplica datos."""
        try:
            kind, session, index, body = unpack(raw)
        except ValueError:
            return None
        if kind == ACK:
            return None
        now = time.monotonic()
        self.closed = {k: v for k, v in self.closed.items() if now - v[0] < 90}
        if kind == FIN and session in self.closed:
            # Un ACK final perdido no obliga a decodificar/guardar dos veces.
            return packet(ACK, session, index, bytes([kind, self.closed[session][1]]))
        self.expire()
        status = 0
        if kind == START:
            size, crc = struct.unpack_from('>II', body)
            if not 1 <= size <= MAX_WIRE:
                status = 1
            elif self.current and self.current['id'] != session:
                status = 2
            elif self.current and (size, crc) != (self.current['size'], self.current['crc']):
                status = 1
            elif not self.current:
                self.current = dict(id=session, size=size, crc=crc, parts={}, received=0, seen=now, started=now)
        elif not self.current or self.current['id'] != session:
            status = 1
        elif kind == DATA:
            current = self.current
            if index >= math.ceil(current['size'] / CHUNK):
                status = 1
            else:
                chunk = body[:min(CHUNK, current['size'] - index * CHUNK)]
                if index in current['parts'] and current['parts'][index] != chunk:
                    status = 1
                else:
                    if index not in current['parts']:
                        # Contador incremental: un reintento no aumenta progreso.
                        current['received'] += len(chunk)
                    current['parts'][index] = chunk
                    self.progress(current['received'], current['size'])
        elif kind == FIN:
            current = self.current
            count = math.ceil(current['size'] / CHUNK)
            if len(current['parts']) != count:
                status = 1
            else:
                data = b''.join(current['parts'][i] for i in range(count))
                try:
                    if zlib.crc32(data) != current['crc']:
                        raise ValueError('CRC-32 incorrecto')
                    self.complete(data, session, time.monotonic() - current['started'])
                except (ValueError, OSError, KeyError, TypeError, struct.error) as exc:
                    status = 1
                    self.progress(0, current['size'], str(exc))
                self.closed[session] = (now, status)
                self.current = None
        if self.current and self.current['id'] == session:
            self.current['seen'] = now
        return packet(ACK, session, index, bytes([kind, status]))


def send_file(endpoint, data, progress=lambda *_: None, deadline=None, retries=4, diagnostics=None):
    """Envía un flujo con ACK por trama y confirmación de guardado en RX.

    endpoint aporta send/receive; retries cuenta repeticiones tras el primer
    intento. deadline, si se proporciona, es un instante monotónico absoluto;
    None permite superar 60 s. diagnostics se actualiza también antes de fallar.
    """
    if not 1 <= len(data) <= MAX_WIRE:
        raise ValueError('Flujo codificado fuera del límite de transporte')
    # Sin plazo global por defecto: una transferencia que avanza puede superar
    # 60 s. Las confirmaciones por fragmento conservan sus esperas y reintentos.
    session = secrets.randbits(32)
    frames = repeats = 0
    stats = diagnostics if diagnostics is not None else {}
    stats.update(sesion=f'{session:08x}', fragmentos_totales=math.ceil(len(data) / CHUNK),
                 fragmentos_confirmados=0, bytes_flujo=len(data), bytes_confirmados=0,
                 tramas_aplicacion=0, reintentos_aplicacion=0,
                 ack_hardware_recibidos=0, ack_hardware_ausentes=0,
                 ack_aplicacion_recibidos=0, intentos_sin_ack_aplicacion=0,
                 respuestas_ajenas=0, respuestas_invalidas=0,
                 ejemplos_respuestas_ajenas=[], ejemplos_respuestas_invalidas=[],
                 escritura_radio_ms=0.0, espera_ack_ms=0.0, latencia_ack_max_ms=0.0)

    def exchange(kind, index=0, body=b''):
        # La respuesta debe coincidir en tipo, sesión, índice y trama confirmada.
        # Un ACK hardware o de otra transacción no acredita este fragmento.
        nonlocal frames, repeats
        stats.update(fase={START: 'START', DATA: 'DATA', FIN: 'FIN'}[kind], indice=index)
        for attempt in range(retries + 1):
            if deadline is not None and time.monotonic() >= deadline:
                raise TimeoutError('Se agotó el plazo total de transmisión')
            frames += 1
            repeats += int(attempt > 0)
            stats.update(tramas_aplicacion=frames, reintentos_aplicacion=repeats)
            sent = time.monotonic()
            acknowledged = endpoint.send(packet(kind, session, index, body))
            stats['escritura_radio_ms'] += (time.monotonic() - sent) * 1000
            stats['ack_hardware_recibidos' if acknowledged else 'ack_hardware_ausentes'] += 1
            end = time.monotonic() + (3 if kind == FIN else 0.4)
            if deadline is not None:
                end = min(deadline, end)
            waiting = time.monotonic()
            try:
                while time.monotonic() < end:
                    raw = endpoint.receive(end - time.monotonic())
                    if raw is None:
                        break
                    try:
                        answer, sid, seq, payload = unpack(raw)
                    except ValueError:
                        stats['respuestas_invalidas'] += 1
                        if len(stats['ejemplos_respuestas_invalidas']) < 4:
                            stats['ejemplos_respuestas_invalidas'].append(raw[:HEADER.size].hex())
                        continue
                    if (answer, sid, seq, payload[0]) == (ACK, session, index, kind):
                        stats['ack_aplicacion_recibidos'] += 1
                        stats['latencia_ack_max_ms'] = max(stats['latencia_ack_max_ms'],
                                                          (time.monotonic() - sent) * 1000)
                        if payload[1]:
                            stats['rechazo_rx'] = payload[1]
                            raise RuntimeError('RX rechazó el archivo o el fragmento; no se confirmó la recepción')
                        return
                    stats['respuestas_ajenas'] += 1
                    if len(stats['ejemplos_respuestas_ajenas']) < 8:
                        stats['ejemplos_respuestas_ajenas'].append(dict(
                            tipo=answer, sesion=f'{sid:08x}', indice=seq,
                            confirma_tipo=payload[0] if answer == ACK else None,
                            sesion_esperada=f'{session:08x}', indice_esperado=index,
                            tipo_esperado=kind))
            finally:
                stats['espera_ack_ms'] += (time.monotonic() - waiting) * 1000
            stats['intentos_sin_ack_aplicacion'] += 1
        raise TimeoutError('RX no confirmó el fragmento dentro del límite de reintentos')

    exchange(START, body=struct.pack('>II', len(data), zlib.crc32(data)))
    for index, offset in enumerate(range(0, len(data), CHUNK)):
        exchange(DATA, index, data[offset:offset + CHUNK])
        stats.update(fragmentos_confirmados=index + 1, bytes_confirmados=min(len(data), offset + CHUNK))
        progress(min(len(data), offset + CHUNK), len(data))
    exchange(FIN)
    return dict(sesion=f'{session:08x}', tramas_aplicacion=frames,
                bytes_tramas_aplicacion=32 * frames, reintentos_aplicacion=repeats,
                confirmado_por_rx=True)
