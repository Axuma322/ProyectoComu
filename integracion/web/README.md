# Interfaz local con Flask — primera versión

TX: Pi Zero W, `lobo@comu-tx.local`. RX: Pi 4 B, `lobor@comu-rx.local`.
El equipo confirmó mensajes `HOLA COMU` recibidos y `ACK=True` usando
`~/prueba_radio.py` y `~/comu-venv`. Esta interfaz no modifica esa prueba ni importa
pyRF24 o gpiozero. No conocemos aún la configuración exacta de ese script remoto.

TX permite cargar BMP/PGM gris de hasta 320×240, elegir una imagen almacenada,
previsualizarla y guardar el modo con/sin pérdidas. La carga viaja solo del teléfono
a su Pi TX. Los originales se conservan; PNG se genera solo para la vista web.
No se cambia tamaño ni se convierte automáticamente una foto a formato de prueba.

El botón de envío está deshabilitado y `/api/transmitir` devuelve 501: todavía no
se integraron transferencia de archivos ni códecs. RX informa que su recepción
no está integrada: imagen y métricas son `null`, no datos de ejemplo. Que el
servidor web responda no demuestra que el radio esté escuchando.

## Instalar sin alterar el entorno de radio

Desde la raíz del repositorio, en cada Pi, comprobar primero:

```bash
hostname
hostname -I
python3 --version
~/comu-venv/bin/python -m pip show pyrf24
```

Usar Python 3.11 o posterior. Crear **otro entorno**, sin cambiar `~/comu-venv`:

```bash
sudo apt install python3-venv python3-pil
python3 -m venv --system-site-packages ~/comu-web-venv
~/comu-web-venv/bin/python -m pip install -r integracion/web/requirements.txt
~/comu-web-venv/bin/python -m pip check
```

Pillow usa el paquete del sistema si satisface el requisito; esto evita tener que
compilar una extensión en la Zero W. Comprobar la resolución de dependencias en
cada placa. Flask y Waitress son dependencias separadas del controlador de radio.
La instalación puede requerir Internet; la ejecución no lo necesita. Para una
instalación completamente offline hay que preparar paquetes para cada arquitectura.

Si los cambios todavía solo están en esta PC, copiar **únicamente esta carpeta**,
sin reemplazar pruebas ni configuración de radio. En cada terminal SSH:

```bash
mkdir -p ~/ProyectoComu/integracion
```

Desde PowerShell, en `D:\ProyectoComu`:

```powershell
scp -r integracion/web lobo@comu-tx.local:~/ProyectoComu/integracion/
scp -r integracion/web lobor@comu-rx.local:~/ProyectoComu/integracion/
```

En ese caso ejecutar los siguientes comandos desde `~/ProyectoComu`. Si el
repositorio tiene otra ruta, usarla consistentemente. No hace falta hacer commit
ni push para copiar estos archivos. Conservar copia si ya existe una versión web
distinta en destino.

## Probar con el Wi-Fi actual

TX, desde la raíz del proyecto:

```bash
~/comu-web-venv/bin/python -m integracion.web --role tx
```

RX, desde su raíz del proyecto:

```bash
~/comu-web-venv/bin/python -m integracion.web --role rx
```

Waitress sirve en el puerto 8080 con un proceso y dos hilos; sin debug, recargador,
radio ni GPIO. Mantener la terminal abierta durante la prueba. Desde Android o iPhone en
la misma red, abrir `http://IP_TX:8080` o `http://IP_RX:8080`, sustituyendo por las
IPv4 reales de `hostname -I`; `0.0.0.0` no es una dirección de navegador.
Si el router aísla clientes, teléfono y Pi no podrán comunicarse aunque vean el
mismo SSID. No se necesita un servidor en la PC. Para detener, Ctrl+C.

Los datos se guardan por defecto en `~/.local/share/proyectocomu-web/`:
`imagenes/` y `seleccion.json`. Se pueden copiar BMP/PGM válidos a `imagenes/`
y recargar la página. `--data-dir /ruta` cambia el almacenamiento. No usar el
mismo directorio para dos procesos TX de prueba simultáneos.

Comprobar desde otra terminal de la misma Pi:

```bash
curl http://127.0.0.1:8080/api/estado
```

En Android, verificar carga válida y vista previa, rechazo de una imagen inválida,
selección persistente tras reiniciar Flask, botón de envío deshabilitado y estado
vacío de RX. Nunca debe aparecer un progreso de transmisión o `ACK=True` generado
por la web. Probar también sin Internet y con pérdida/recuperación de Wi-Fi.

## Integración y red: próximos pasos

El proceso de radio será el único dueño de SPI y GPIO. Web y botón físico usarán
la misma cola de órdenes; definiremos prioridad entre DIP y selección web antes
de permitir envíos. Se conservan GPIO17 de inicio, GPIO23/24/25 de LED y
GPIO27/5/6/13 del DIP. No ejecutar dos procesos que controlen esos pines o el radio.

No hay llamadas HTTP entre Pi. El flujo de imágenes entre extremos seguirá
siendo nRF24; los estados web vendrán de la integración real, no de temporizadores.

Para los AP se propone `Comu-TX` → `192.168.50.1` y `Comu-RX` → `192.168.60.1`,
puerto web 8080. Antes hay que revisar OS/NetworkManager y `iw list` de **cada**
placa: RX ya no es una Zero W. Guardar perfil y UUID del Wi-Fi actual, crear AP
sin autoconexión, programar reversión independiente de SSH y probar únicamente TX.
No basta con conservar la sesión: activar AP puede desconectarla. Confirmar SSH
por la IP nueva y el retorno a la red anterior antes de habilitar persistencia.
Mantener consola local como respaldo. Los comandos detallados de red se cerrarán
con el diagnóstico real; esta versión no contiene scripts que activen AP.

Después de validar web y red prepararemos servicios systemd con usuario normal,
`Restart=on-failure`, sin arranque de la prueba de texto en lugar del protocolo.
No se instala ni habilita todavía ningún servicio automático.

## Verificación y fuentes

```bash
~/comu-web-venv/bin/python -m unittest integracion.web.test_web -v
```

Las pruebas usan HTTP local y archivos temporales, no radios ni resultados RF.
La prueba desde teléfonos y sobre ambas Pi debe registrarse por separado.

- [Flask: instalación](https://flask.palletsprojects.com/en/stable/installation/).
- [Flask: cargas de archivos](https://flask.palletsprojects.com/en/stable/patterns/fileuploads/).
- [Flask: Waitress](https://flask.palletsprojects.com/en/stable/deploying/waitress/).
- [Pillow: lectura de imágenes](https://pillow.readthedocs.io/en/stable/reference/Image.html).

La web está pensada para la red de prueba de confianza; no incorpora cuentas de
usuario. Un token de página protege modificaciones frente a peticiones externas
sin cargar primero la interfaz. No publicar el puerto 8080 en Internet.

## Diagnóstico común de los AP (26 de noviembre)

El requisito es conexión normal desde navegador Android o iPhone: Wi-Fi de 2,4 GHz,
WPA2-Personal/RSN con AES/CCMP, DHCP y HTTP local. SSID visible, sin lista de MAC
permitidas ni necesidad de desactivar direcciones privadas, instalar apps, asignar
IP manual o aplicar ajustes de fabricante. Se puede aceptar el aviso estándar
de red sin Internet; no se falsearán las comprobaciones del sistema ni se añadirá
un portal cautivo. El ancho de referencia será 20 MHz, sujeto al soporte real.

Evidencia comunicada: TX activó `Comu-TX`, dnsmasq concedió `192.168.50.16` a la
laptop y la recuperación volvió a `PISO 3`. El teléfono intentó conectar sin error
visible; no se confirmó su IP y el SSID aparecía/desaparecía. No hay archivos del
journal en el repositorio ni acceso SSH autenticado desde esta sesión. La laptop
prueba WPA/DHCP para ese cliente en ese momento, no la conexión del teléfono.

Antes de cambiar configuración hay que distinguir: caída del AP; fallo de
asociación/WPA; DHCP incompleto; abandono de red sin Internet; HTTP no disponible.
La desaparición del SSID exige correlacionar el temporizador y estados del AP con
lo observado también en la laptop. Flask no impide autenticarse por Wi-Fi, pero
si termina al perder SSH explicaría un fallo posterior de HTTP. Un intercambio
WPA fallido no demuestra automáticamente que la clave introducida sea incorrecta.
Se conserva PMF `1` (deshabilitado), porque ya permitió arrancar y conectar la laptop.

### Leer evidencias sin activar el AP

`diagnostico_ap.py` usa solo biblioteca estándar y comandos de lectura. No cambia
perfiles/servicios, no hace escaneos activos, no importa radio/GPIO ni eleva su
propio nivel de privilegios. Se ejecuta con sudo para poder leer journal/estaciones.
Ejemplo, después de copiarlo a TX, desde la raíz del proyecto en `PISO 3`:

```bash
COMU_PREVIO="/var/tmp/comu-ap-previo-$(date +%Y%m%d-%H%M%S)"
sudo /usr/bin/python3 integracion/web/diagnostico_ap.py \
  --profile Comu-TX --interface wlan0 --history-minutes 120 \
  --duration 0 --output "$COMU_PREVIO"
sudo cat "$COMU_PREVIO/estado.jsonl"
sudo cat "$COMU_PREVIO/eventos.jsonl"
systemctl list-timers --all --no-pager
sudo ss -ltnp '( sport = :8080 )'
```

El directorio debe ser nuevo; queda privado y no se sobrescribe. `estado.jsonl`
registra campos permitidos del perfil (sin PSK), modo/canal/ancho, estaciones y su
autorización cuando el controlador la informa, IP/vecinos y código HTTP de localhost.
Los errores de comandos se conservan como códigos: falta de permisos/herramientas
no se interpreta como fallo de conexión. `http_local: 200` no prueba acceso desde
el teléfono ni estado del radio.

`eventos.jsonl` extrae tipos de evento, fecha UTC, MAC/IP y códigos; no guarda el
texto íntegro del journal, contraseñas, cuerpos HTTP ni capturas EAPOL. No usar
`--show-secrets`, volcados de `.nmconnection` o registro de claves. Historial:
arranque actual, intervalo solicitado y últimos 5000 registros de las fuentes
seleccionadas. Un archivo vacío no prueba ausencia de intentos: pueden faltar
eventos, permisos o haber rotado el journal. Los arranques anteriores se revisan aparte.

### Mantener Flask sin SSH

La plantilla `comu-web@.service` está preparada, no instalada ni habilitada. Usa
un usuario normal, escucha `0.0.0.0:8080`, reinicia ante fallo y no depende del
perfil Wi-Fi ni de SSH. Supone `/home/USUARIO/ProyectoComu` y el entorno separado
`/home/USUARIO/comu-web-venv`: comprobar rutas y dependencias antes de instalar.
Si ya existe un servicio funcional, revisarlo y conservarlo; no abrir dos servidores.

Para TX requiere `/etc/proyectocomu/web-lobo.env` con una sola línea `COMU_ROLE=tx`.
Una vez revisado el proceso actual y aprobada la instalación, copiar la plantilla
a systemd, validar con `systemd-analyze verify` y arrancar `comu-web@lobo.service`
mediante `start`, sin `enable`. Para RX, más adelante, misma plantilla con instancia
`lobor` y rol `rx`; no se instala nada en RX durante el diagnóstico TX.

Primero probar supervivencia en `PISO 3`: comprobar servicio y HTTP, cerrar SSH,
volver a entrar y comparar PID/reinicios/respuesta. Comandos de comprobación:

```bash
systemctl show comu-web@lobo.service -p ActiveState -p MainPID -p NRestarts
curl --connect-timeout 3 -fsS http://127.0.0.1:8080/api/estado
```

### Ensayo reversible de 30 minutos

Antes de activar: leer configuración del temporizador existente y verificar que
su acción vuelve al perfil original de `PISO 3`. Ampliarlo temporalmente a 30 minutos
sin sustituir su acción ni dejar otro disparador más corto. Confirmar con
`list-timers` el tiempo restante. Los comandos de ajuste se cerrarán al conocer
la unidad realmente instalada; no se asume un nombre ni se crea otra recuperación
que pueda competir. Mantener consola local de respaldo; no reiniciar en este ensayo.

Después de revisar esos datos, el observador puede seguir 40 minutos independiente
de SSH. Este ejemplo solo registra; no activa AP ni configura autoarranque:

```bash
COMU_OBS="/var/tmp/comu-ap-ensayo-$(date +%Y%m%d-%H%M%S)"
sudo systemd-run --unit=comu-ap-observar --collect \
  --property=Type=exec --property=RuntimeMaxSec=41min \
  /usr/bin/python3 "$PWD/integracion/web/diagnostico_ap.py" \
  --profile Comu-TX --interface wlan0 --history-minutes 5 \
  --duration 2400 --output "$COMU_OBS"
printf 'Captura: %s\n' "$COMU_OBS"
```

Anotar ruta y comprobar `systemctl status comu-ap-observar.service`. No usar
`--scope`, `--pty` o `--pipe`, que lo vincularían a la ejecución interactiva.
El registro no aumenta el nivel de NetworkManager: si es insuficiente, preparar
otro ensayo con dominios de depuración acotados y restauración del nivel anterior.

Tiempo previsto: 0–5 min laptop; 5–10 primer teléfono; 10–15 otro teléfono,
preferiblemente del otro sistema; 15–20 un tercer cliente o repetición;
20–25 varios clientes simultáneos; 25–30 observación y recuperación automática.
Conservar canal/cifrado/PMF durante ese ensayo. No cambiar nRF24 ni su potencia.
Anotar por intento: etiqueta A/B/C, hora, SSID visible, resultado de conexión,
MAC usada en esa red, IP y resultado HTTP. No se necesitan contraseñas en el informe.

| Evidencia | Interpretación |
|---|---|
| SSID desaparece para todos y AP se desactiva | Correlacionar recuperación, controlador y alimentación |
| Fallos WPA sin autorización | Revisar negociación y perfil guardado, no culpar automáticamente a la clave |
| Estación autorizada sin concesión | Revisar DISCOVER/OFFER/REQUEST/ACK y permanencia del enlace |
| DHCPACK para MAC del teléfono | El servidor concedió IP; contrastar recepción/uso en el teléfono |
| IP obtenida y posterior desconexión | Posible política de cliente; la Pi sola no demuestra rechazo por falta de Internet |
| IP válida, laptop abre HTTP y teléfono no | Revisar ruta/proxy/VPN/navegador antes de cambiar WPA |

No inferir causa por un `reason` numérico aislado. HTTP debe abrirse por dirección
numérica: `http://192.168.50.1:8080` y `/api/estado`. El teléfono debe obtener
`192.168.50.x/24`, distinta de `.1`, red y broadcast; `169.254.x.x` no acredita DHCP.
No asignar IP manual para ocultar el fallo. Laptop Windows: `curl.exe --connect-timeout 5
http://192.168.50.1:8080/api/estado` (en una sola línea).

Tras volver a `PISO 3`, conservar ambos JSONL y restaurar la duración original del
temporizador y cualquier preparación temporal. Mantener su acción y los perfiles.
Repetir después en RX con `Comu-RX` y `192.168.60.1`, sin asumir que su controlador
se comporta igual. No se habilita AP ni servicio web automáticamente en esta etapa.

Fuentes: [NetworkManager](https://networkmanager.dev/docs/api/latest/nm-settings-nmcli.html),
[registro](https://networkmanager.dev/docs/api/latest/NetworkManager.conf.html),
[Android: DHCP y validación](https://source.android.com/docs/core/ota/modular-system/networking),
[Apple: WPA2 AES, SSID y filtrado MAC](https://support.apple.com/en-us/102766),
[systemd](https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html).

Pruebas del observador: `python3 -m unittest integracion.web.test_diagnostico_ap -v`.
Usan fixtures sintéticos, no representan conexiones reales de teléfonos.
