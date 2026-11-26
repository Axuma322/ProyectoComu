# Guía de operación y mantenimiento

## Uso normal

| Equipo | Red abierta | Página | SSH |
|---|---|---|---|
| TX Zero W | `Comu-TX` | http://192.168.50.1:8080 | `ssh lobo@192.168.50.1` |
| RX Pi 4 B | `Comu-RX` | http://192.168.60.1:8080 | `ssh lobor@192.168.60.1` |

Encender ambas, conectar cada teléfono a la red correspondiente y permanecer
conectado si avisa que no hay Internet. En TX el teléfono carga o elige el
BMP/PGM gris de hasta 320 × 240; el modo se pone con el DIP y se transmite con
el botón físico (la página muestra lo que marcan los switches). Probar
compresión es opcional. Con `--gpio`, RX arranca en pausa: presionar su botón
una vez para habilitar la recepción (el verde empieza a latir). RX guarda las
recepciones en su galería. Borrar en una Raspberry
no borra la copia de la otra. No cerrar la alimentación durante guardados;
al terminar se puede apagar desde SSH con `sudo systemctl poweroff`.

La web y el radio son servicios independientes. El AP permanente arranca al
encender; no vuelve a PISO 3 después de cinco minutos. La
[guía de redes](despliegue/redes_definitivas.md) conserva activación y recuperación.

## Consulta y diagnóstico

Estos comandos Linux sirven en cualquiera de las dos placas, conectado con su
usuario normal. Comprobar `hostname` antes de acciones administrativas:

```bash
hostname
systemctl status "comu-web@$(id -un).service" "comu-enlace@$(id -un).service" --no-pager
curl --connect-timeout 3 -fsS http://127.0.0.1:8080/api/estado
journalctl -u "comu-enlace@$(id -un).service" -n 50 --no-pager
vcgencmd get_throttled
```

HTTP 200 prueba la web local. `radio_integrado` y un heartbeat reciente prueban
disponibilidad del worker local. La entrega requiere `confirmado_por_rx=true`
en TX y archivo/historial de RX. Reintentos hardware y de aplicación no son
reinicios; PSNR en dB describe reconstrucción, no señal RF; BER físico no se mide.

Los resultados TX están en `~/.local/share/proyectocomu-web/resultados/`.
Guardar el JSON del trabajo y su recepción correspondiente en
`~/.local/share/proyectocomu-web/recepciones/` de RX. Anotar imagen, modo/bits,
distancia, alimentación, tiempo, resultado y condiciones por intento.
Los logs pueden requerir `sudo` si el usuario no tiene acceso al journal.

No existe corte global de 60 s. Un fallo por falta de confirmación todavía puede
ocurrir tras agotar reintentos de una trama; conservar su diagnóstico. RX también
descarta transferencias tras 10 s sin fragmentos. Se puede repetir manualmente
un envío fallido; no existe reanudación automática de una sesión anterior.

Para cargar cambios, sin envío en curso:

```bash
sudo systemctl restart "comu-web@$(id -un).service" "comu-enlace@$(id -un).service"
```

Esto no cambia Wi-Fi. No iniciar en paralelo `prueba_radio.py`, la prueba mínima
ni otro worker. Para desarrollo en PISO 3, recuperar cada placa desde su AP con
el comando correspondiente de [redes definitivas](despliegue/redes_definitivas.md).
No basta conectar un cable USB para obtener una interfaz de red USB: esa función
no se configuró como parte de este despliegue.

## GPIO persistentes

Aplicar **después de comprobar el montaje** con la
[guía de LED, botón y DIP](hardware/guia_led_botones.md). La plantilla actual
no pasa `--gpio`. Este procedimiento añade un archivo específico, sin cambiar
Wi-Fi ni la plantilla compartida. Ejecutar en cada placa con su usuario normal;
no sobreescribir un `gpio.conf` anterior sin conservarlo:

```bash
COMU_UNIDAD="comu-enlace@$(id -un).service"
COMU_GPIO_DIR="/etc/systemd/system/${COMU_UNIDAD}.d"
sudo mkdir -p "$COMU_GPIO_DIR"
sudo tee "$COMU_GPIO_DIR/gpio.conf" >/dev/null <<'EOF'
[Service]
ExecStart=
ExecStart=/home/%i/comu-web-venv/bin/python -m integracion.enlace --role ${COMU_ROLE} --gpio
EOF
sudo systemctl daemon-reload
sudo systemctl restart "$COMU_UNIDAD"
systemctl cat "$COMU_UNIDAD"
curl --connect-timeout 3 -fsS http://127.0.0.1:8080/api/estado
```

`%i` toma el usuario de la instancia y `COMU_ROLE` proviene del archivo de entorno
ya instalado. La línea vacía de `ExecStart=` reemplaza la orden anterior, como
define [systemd.service](https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html#ExecStart=).
Comprobar servicio activo y `enlace.gpio=true`; después validar un encendido.
La limitación actual del LED azul RX sigue documentada en la guía física.

Para retirar únicamente este ajuste, en la misma placa y sin transmisión:

```bash
COMU_UNIDAD="comu-enlace@$(id -un).service"
sudo rm -f "/etc/systemd/system/${COMU_UNIDAD}.d/gpio.conf"
sudo systemctl daemon-reload
sudo systemctl restart "$COMU_UNIDAD"
```

No borra otros ajustes de systemd. Si se había conservado un `gpio.conf` previo,
restaurarlo en lugar de quitarlo. Ninguno de estos comandos se ejecuta por leer
la documentación; esta revisión no activa GPIO ni reinicia las placas.

## Respaldo y pruebas

Los datos están fuera del checkout. Antes de actualizar guardar código y datos
con servicios detenidos o durante un periodo sin actividad; no reemplazar los
entornos de radio ni perfiles de red. `instalar_imagenes.sh` corresponde al paquete
preparado para la instalación original, no a una actualización automática desde Git.

Los [informes](README.md) conservan mediciones y respaldos concretos de cada ronda.
Para ejecutar pruebas de software en una copia de desarrollo, sin abrir hardware:

```bash
~/comu-web-venv/bin/python -m unittest \
  transmision.test_minimo transmision.test_imagenes integracion.test_senales \
  integracion.web.test_web integracion.web.test_red_local \
  integracion.web.test_diagnostico_ap -v
```

Las pruebas unitarias con canal artificial no sustituyen las de radio ni las de
cableado. No hacer commits o push desde scripts de despliegue: revisar antes el
diff, los archivos de diagnóstico y los datos que se decida compartir.
