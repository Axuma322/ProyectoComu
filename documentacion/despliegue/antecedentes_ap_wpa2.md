# Antecedentes del diagnóstico Wi-Fi con WPA2

Archivo histórico, conservado el 26 de noviembre de 2026. El texto siguiente
describe observaciones y propuestas anteriores a la decisión de usar redes
abiertas. Los plazos y comandos de ensayo aquí incluidos no son la configuración
vigente ni prueban que cada propuesta se ejecutara. La operación actual está
en [redes definitivas](redes_definitivas.md).

## Diagnóstico histórico de autenticación (sustituido por redes abiertas)

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
