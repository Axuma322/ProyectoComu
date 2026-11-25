# Prueba mínima con Python y pyRF24

Kit K3 confirmado: dos Raspberry Pi Zero W, dos radios nRF24 con antenas
externas, dos protoboards y cables. **Todavía no se ha probado este código en
hardware.** Esta iteración solo inicializa los radios y envía texto corto.
No implementa imágenes, compresión, archivos ni el protocolo propuesto.

## Antes de conectar

Identificar el módulo, su pinout, polaridad, tensión y corriente máxima en TX/RX.
La antena externa no confirma que tenga PA/LNA ni que sea variante «+».
No alimentar el radio hasta verificar esos datos. No aplicar 5 V al chip ni a los
GPIO. Si hay un adaptador con regulador, comprobar su entrada permitida por separado.
Definir una fuente adecuada, GND común y desacoplamiento según el módulo.
Revisar las conexiones con las fuentes desconectadas y colocar las antenas
compatibles antes de transmitir. El nivel LOW del programa no garantiza un consumo
seguro ni una potencia concreta para un módulo todavía sin identificar.

Cableado de señales propuesto, en cada Pi (numeración BCM):

| Radio | GPIO BCM | Pin físico |
|---|---:|---:|
| CE | 22 | 15 |
| CSN | 8 / SPI0 CE0 | 24 |
| SCK | 11 | 23 |
| MOSI | 10 | 19 |
| MISO | 9 | 21 |
| GND | Tierra común | 25 |
| VCC | **Pendiente de verificar alimentación** | No conectar aún |

IRQ no se usa. Confirmar orientación del conector del radio y que las Pi tengan
el cabezal GPIO instalado y bien soldado. CSN no es CE: `csn=0` selecciona
`/dev/spidev0.0` (GPIO8); `csn=1`, `/dev/spidev0.1` (GPIO7).
SCK/MOSI/MISO corresponden al SPI0 hardware y no se reasignan desde Python.

## Instalación en ambas Pi

Usar Raspberry Pi OS Lite **de 32 bits compatible con la Zero W original**.
La Zero W usa ARMv6; no confundirla con la Zero 2 W ni instalar un wheel aarch64.
Consultar en cada placa:

```bash
uname -m
python3 --version
cat /etc/os-release
sudo apt update
sudo apt install python3-venv python3-pip
sudo raspi-config nonint do_spi 0
sudo reboot
```

Tras reiniciar, desde la raíz del repositorio `ProyectoComu`:

```bash
ls -l /dev/spidev0.*
python3 -m venv .venv
source .venv/bin/activate
```

### Compatibilidad ARMv6 (consulta: 8 de noviembre de 2026)

La documentación de pyRF24 no promete wheels oficiales para ARMv6.
Sin embargo, piwheels lista **pyrf24 0.4.1, linux_armv6l, para CPython 3.9 y 3.11**.
En esos intérpretes se puede intentar la instalación binaria explícita:

```bash
python -m pip install --only-binary=:all: --index-url https://www.piwheels.org/simple 'pyrf24==0.4.1'
python -c "import pyrf24; print('Backend:', pyrf24.RF24_DRIVER)"
```

No se encontró un wheel ARMv6 de esa versión para Python 3.13. La etiqueta del
paquete no sustituye la comprobación de importación en la Pi: también importan
la ABI de Python y las bibliotecas del sistema. Si no hay paquete compatible,
falla la carga o aparece `Illegal instruction`, usar la alternativa siguiente.
No renombrar un wheel ARMv7/aarch64 para forzar su instalación.

### Alternativa: compilar en la propia Zero W

Con el entorno anterior activo, estas instrucciones siguen la instalación desde
fuentes de pyRF24 y fijan la versión 0.6.0 (Python >=3.9). No se ha compilado aquí
en ARMv6: es la alternativa por validar en el equipo, no una instalación garantizada.

```bash
sudo apt install git build-essential cmake python3-dev
git clone --branch v0.6.0 --recurse-submodules https://github.com/nRF24/pyRF24.git /tmp/pyRF24-k3
export CMAKE_ARGS='-DRF24_DRIVER=SPIDEV'
export CMAKE_BUILD_PARALLEL_LEVEL=1
python -m pip install --no-cache-dir -v /tmp/pyRF24-k3
python -c "import pyrf24; print('Backend:', pyrf24.RF24_DRIVER)"
```

La ruta temporal debe estar libre. Compilar en la Zero puede tardar bastante;
un solo trabajo reduce el uso de sus 512 MB de RAM. Si falta memoria o falla la
compilación, conservar el error completo y registrar OS, Python y arquitectura.
No instalar con `sudo pip` ni usar `--break-system-packages`.

## Configuración y ejecución

Copiar el repositorio a ambas Pi y usar el mismo `transmision/config.json`:
CE BCM22, CSN 0, SPI 1 MHz, canal 40 (2440 MHz), tasa 1 Mbit/s y dirección
ASCII `K3T01` de cinco bytes. El canal es una elección inicial, no una prueba de
ausencia de interferencia ni de cumplimiento normativo; validarlo con el laboratorio.
250 kbit/s solo se admite cuando el controlador identifica la variante «+».

Ambos extremos fijan carga de 32 bytes, CRC de 16 bits, auto-ACK, nivel LOW y
cinco reintentos de radio separados por 1500 µs. El mensaje ocupa de 1 a 32 bytes
UTF-8, sin NUL; se completa con ceros. No hay fragmentación ni reintentos de aplicación.

Desde la raíz del repositorio, ejecutar primero el diagnóstico **en ambas Pi**:

```bash
.venv/bin/python -m transmision.diagnostico
```

Después iniciar el receptor y dejarlo escuchando:

```bash
.venv/bin/python -m transmision.receptor.escuchar
```

En la otra Pi, enviar un mensaje:

```bash
.venv/bin/python -m transmision.transmisor.enviar --message 'Hola K3'
```

Terminar RX con Ctrl+C. Si hay errores de permisos, revisar acceso a SPI y GPIO:
el backend SPIDEV también necesita controlar CE. Para el diagnóstico inicial se
puede ejecutar el mismo comando con `sudo .venv/bin/python ...`, conservando el
intérprete del entorno. No cambiar permisos globales de dispositivos a `777`.

Todos aceptan `--config ruta.json`, `--ce-pin`, `--csn`, `--spi-speed`, `--channel`,
`--data-rate` y `--address`; `--help` muestra las opciones sin cargar pyRF24.
Ejemplo: añadir `--channel 45 --data-rate 1MBPS --address K3T01` en TX y RX.
Los pines dependen del cableado local; canal, tasa y dirección deben coincidir.

## Qué comprobar y registrar

1. Diagnóstico correcto en cada placa: demuestra acceso local por SPI, no enlace.
2. RX muestra `Hola K3` y los bytes hexadecimales correspondientes.
3. TX recibe ACK. Ese ACK confirma al radio remoto, no que Linux haya mostrado el
   mensaje. Si no llega ACK, el mensaje podría haber llegado y haberse perdido la respuesta.
4. Repetir varios envíos con RX arrancado primero; registrar también los fallos.

Registrar módulos, fuente/tensión, pinout, distancia, configuración, versión de
pyRF24 y salida de consola. Ante fallos revisar alimentación durante TX/ACK,
cables cortos, SPI, CE/CSN, antenas y parámetros comunes antes de subir potencia.
Las lecturas de software no identifican por sí solas la placa comercial.

Pruebas de lógica sin radio (simuladas, no validan hardware):

```bash
python3 -m unittest transmision.test_minimo -v
```

## Fuentes

- [pyRF24: instalación y compilación](https://pyrf24.readthedocs.io/en/latest/).
- [Disponibilidad de wheels en piwheels](https://www.piwheels.org/project/pyrf24/)
  y [explicación de ARMv6/ARMv7](https://www.piwheels.org/faq.html).
- [Ejemplo oficial 0.4.1](https://github.com/nRF24/pyRF24/blob/v0.4.1/examples/getting_started.py)
  y [API RF24](https://pyrf24.readthedocs.io/en/latest/rf24_api.html).
- [Fuentes de compilación 0.6.0](https://github.com/nRF24/pyRF24/tree/v0.6.0).

La documentación anterior conserva la propuesta C++/RF24 y el protocolo futuro.
Esta prueba usa Python/pyRF24 por decisión de esta iteración; no modifica esa investigación.

## Primera prueba en hardware (24 de noviembre)

Se instalaron las dos tarjetas con **Raspberry Pi OS (Legacy, 32-bit) Lite**, que es Bookworm con Python 3.11.2. Se escogió esa versión justamente por lo que se explica arriba: piwheels tiene pyRF24 0.4.1 para ARMv6 solo hasta Python 3.11, y la versión actual del sistema trae 3.13. Así no hubo que compilar nada.

Lo que funcionó en ambas Pi, desde la raíz del repo:

```bash
sudo raspi-config nonint do_spi 0
sudo apt install -y git python3-venv python3-pip python3-gpiozero
python3 -m venv --system-site-packages .venv
.venv/bin/pip install --only-binary=:all: --index-url https://www.piwheels.org/simple 'pyrf24==0.4.1'
```

`--system-site-packages` es para que el entorno también vea gpiozero, que se usa para los LED y el botón. La importación devolvió `Backend: SPIDEV` y aparecen `/dev/spidev0.0` y `/dev/spidev0.1`. El usuario por defecto ya está en el grupo `spi`, así que no hizo falta `sudo` para correr el diagnóstico.

Con un radio conectado a `dinamita`, `diagnostico.py` respondió bien: inicializa por SPI, identifica el modelo como nRF24L01+ y muestra el LNA habilitado, con canal 40, 1 Mbit/s y potencia LOW según `config.json`. Todavía no se ha probado el envío entre dos radios; eso queda pendiente hasta tener la segunda Pi funcionando o conectar los dos radios a la misma Pi.

Un detalle de la red: el nombre `.local` no resolvió en la red de prueba, así que para entrar por SSH se buscó la IP de cada Pi con un barrido de ping y `arp` (las Pi Zero W tienen MAC que empieza en `b8:27:eb`).
