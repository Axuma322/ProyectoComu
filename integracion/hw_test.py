#!/usr/bin/env python3
"""Prueba de LEDs, botón y DIP switch (IE0527 - Transmisión inalámbrica de imágenes).

Uso:  python3 hw_test.py
- Al iniciar, enciende los LED uno por uno (verde, azul, rojo).
- Luego muestra en pantalla el estado del botón y del DIP switch.
- Al presionar el botón, los tres LED parpadean.
Ctrl+C para salir.
"""
from gpiozero import LED, Button
from time import sleep

# --- Asignación de pines (numeración BCM) ---
LED_ACT = LED(23)    # verde: actividad (TX/RX)
LED_MODO = LED(24)   # azul: modo con pérdidas
LED_FIN = LED(25)    # rojo: fin / error
BOTON = Button(17, pull_up=True, bounce_time=0.05)

# DIP switch (solo transmisor). Si no está conectado, leerá todo OFF.
DIP_PINES = {"1_modo": 27, "2_calidad_b1": 5, "3_calidad_b0": 6, "4_auto": 13}
DIP = {k: Button(p, pull_up=True) for k, p in DIP_PINES.items()}


def leer_dip():
    # Con pull-up: interruptor en ON conecta a GND -> is_pressed = True
    return {k: int(b.is_pressed) for k, b in DIP.items()}


def secuencia_inicio():
    for led in (LED_ACT, LED_MODO, LED_FIN):
        led.on(); sleep(0.4); led.off()


def al_presionar():
    print(">> Botón presionado")
    for _ in range(3):
        for led in (LED_ACT, LED_MODO, LED_FIN):
            led.on()
        sleep(0.15)
        for led in (LED_ACT, LED_MODO, LED_FIN):
            led.off()
        sleep(0.15)


BOTON.when_pressed = al_presionar

print("Probando LEDs: verde, azul, rojo...")
secuencia_inicio()
print("Listo. Mueva los interruptores del DIP y presione el botón (Ctrl+C para salir).")

ultimo = None
try:
    while True:
        d = leer_dip()
        if d != ultimo:
            calidad = d["2_calidad_b1"] * 2 + d["3_calidad_b0"]
            modo = "CON pérdidas" if d["1_modo"] else "SIN pérdidas"
            auto = "AUTO" if d["4_auto"] else "manual"
            print(f"DIP {d} -> modo {modo}, calidad nivel {calidad}, selección {auto}")
            LED_MODO.value = d["1_modo"]  # azul encendido = con pérdidas
            ultimo = d
        sleep(0.1)
except KeyboardInterrupt:
    print("\nFin de la prueba.")
