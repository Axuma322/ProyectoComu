"""Patrones de los LED de TX y RX.

La lógica está separada del GPIO: patron() solo decide qué LED va encendido en
un instante dado, así se puede probar sin la Raspberry. Senales corre un hilo
que consulta ese patrón cada 50 ms y mueve los LED reales.
"""
import threading
import time

LATIDO = 2.0        # periodo del destello de "estoy vivo"
EXITO = 1.2         # duración de los 3 destellos al completar
ERROR_RAPIDO = 5.0  # segundos de parpadeo rápido antes de quedar fijo
AVISO = 1.0         # destellos rojos cuando se presiona sin imagen


def patron(estado, modo, dip, t, dt, aviso_dt=None):
    """Devuelve (verde, azul, rojo) para el instante t.

    estado: fase publicada por el enlace; dt: segundos desde que empezó esa fase.
    modo: último modo resuelto (lo que se envió o recibió).
    dip: dict con 'modo' leído de los switches en TX, o None en RX.
    aviso_dt: segundos desde la última pulsación inválida, o None.
    """
    latido = (t % LATIDO) < 0.1

    if estado in ('esperando', 'escuchando'):
        verde = latido
    elif estado == 'codificando':
        verde = (t % 0.2) < 0.1
    elif estado in ('enviando', 'recibiendo'):
        verde = True
    elif estado == 'completado':
        verde = (dt % 0.4) < 0.2 if dt < EXITO else latido
    else:
        verde = False

    if estado == 'error':
        rojo = (dt % 0.25) < 0.125 if dt < ERROR_RAPIDO else True
    elif estado in ('error_radio', 'detenido'):
        rojo = True
    else:
        rojo = False
    # La pulsación sin imagen se nota aunque el enlace siga esperando
    if aviso_dt is not None and aviso_dt < AVISO:
        rojo = (aviso_dt % 0.2) < 0.1

    # Azul: en TX, mientras espera, muestra lo que va a usar el botón (DIP).
    # Durante un envío, y siempre en RX, muestra el modo real de la imagen.
    if dip and estado in ('esperando', 'completado', 'error'):
        elegido = dip.get('modo')
    else:
        elegido = modo
    if elegido == 'automatico':
        azul = (t % 1.0) < 0.5
    else:
        azul = elegido == 'con_perdidas'

    return verde, azul, rojo


class Senales:
    def __init__(self, verde, azul, rojo):
        self.leds = (verde, azul, rojo)
        self._lock = threading.Lock()
        self._estado = 'iniciando_radio'
        self._desde = time.monotonic()
        self._modo = None
        self._dip = None
        self._aviso = None
        self._parar = threading.Event()
        self._barrido()
        self._hilo = threading.Thread(target=self._ciclo, name='comu-leds', daemon=True)
        self._hilo.start()

    def _barrido(self):
        # Al arrancar: verde, azul, rojo una vez, para ver que los tres sirven
        for led in self.leds:
            led.on()
            time.sleep(0.25)
            led.off()

    def mostrar(self, estado, modo=None, dip=None):
        with self._lock:
            if estado != self._estado:
                self._estado = estado
                self._desde = time.monotonic()
            if modo:
                self._modo = modo
            self._dip = dip

    def aviso(self):
        with self._lock:
            self._aviso = time.monotonic()

    def _ciclo(self):
        while not self._parar.wait(0.05):
            ahora = time.monotonic()
            with self._lock:
                aviso_dt = ahora - self._aviso if self._aviso else None
                valores = patron(self._estado, self._modo, self._dip,
                                 ahora, ahora - self._desde, aviso_dt)
            for led, encendido in zip(self.leds, valores):
                led.value = encendido

    def cerrar(self):
        self._parar.set()
        self._hilo.join(timeout=1)
        for led in self.leds:
            led.off()
