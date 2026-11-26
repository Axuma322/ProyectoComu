# Wi-Fi definitivo: AP abiertos independientes

**Revisión del 26 de noviembre:** la primera activación permanente terminó con
resultado 0 en TX y RX. Después se volvió a PISO 3 para actualizar el software y
se entregaron comandos de reactivación permanente. El equipo reportó luego éxito
en ambos modos a unos 25 m. El [procedimiento de operación y recuperación](../../documentacion/despliegue/redes_definitivas.md)
describe el acceso actual; este documento conserva la preparación y el ensayo
inicial, cuyas instrucciones de permanecer en PISO 3 pertenecen a aquella fase.

Decisión del equipo del 26 de noviembre de 2026. Se abandona la investigación de
WPA: ambas redes serán abiertas. La prueba real de `Comu-TX-Prueba` permitió
conectar teléfono y tablet, abrir Flask y cargar una imagen BMP desde el teléfono.
Ese perfil fue temporal (`save no`); no se reutiliza su UUID ni se presupone que
exista después del reinicio.

| Rol | Hardware | Usuario / hostname | SSID | Dirección | Canal propuesto |
|---|---|---|---|---|---|
| TX | Pi Zero W | lobo / comu-tx | Comu-TX | 192.168.50.1/24 | 1 |
| RX | Pi 4 B | lobor / comu-rx | Comu-RX | 192.168.60.1/24 | 11 |

Ambas usan `bg` (2,4 GHz), DHCP de NetworkManager (`ipv4.method shared`) y HTTP
en 8080. No se necesita Internet, router ni PC para operar. La PC se utiliza
para instalar y comprobar. No hay HTTP entre las Raspberry: las imágenes entre
extremos seguirán viajando exclusivamente por nRF24. No se cambia radio, potencia,
canal RF, botones, DIP, LED, transmisión o codificación.

El canal 11 de RX separa sus emisiones Wi-Fi de las de TX. Debe comprobarse con
`sudo iw phy phy0 info` en RX. No garantiza ausencia de interferencia con nRF24;
su configuración real se conserva sin inferirla de la configuración del repositorio.

## Estado comprobado de TX durante la preparación

Se conserva `netplan-wlan0-PISO 3`, UUID
`f9713ac8-75f0-30b3-8a7a-5ba003dc9ef0`, y el script existente
`/usr/local/sbin/comu-tx-rollback` sin modificaciones.

Se creó **otro perfil persistente**, `ProyectoComu-AP-TX`, UUID
`63964f31-11cd-4504-9e8f-ab71ec779a5d`, con SSID `Comu-TX`, abierto y autoconexión
inicialmente deshabilitada. El antiguo perfil protegido `Comu-TX` se conserva.
Se instaló y habilitó `comu-web@lobo.service`; sustituyó al servicio transitorio
`comu-web-tx-prueba.service`. Se verificaron HTTP 200, rol TX y selección de la BMP
anterior. Después se comprobó un reinicio real: el equipo confirmó desde el teléfono
SSID `Comu-TX` y HTTP funcionando. El observador registró 53 lecturas en modo AP,
52 con HTTP 200. La recuperación terminó con código 0 y volvió a PISO 3; Flask
continuó activo sin reinicios. Se registró el ensayo como validado y se dejó
`connection.autoconnect=no` en el AP, por decisión del equipo para continuar
programando por PISO 3.

## Preparación y prueba de RX

Se comprobó una Pi 4 Model B Rev 1.4 con Raspbian Trixie y NetworkManager 1.52.1.
El canal 11 (2462 MHz) está permitido. El UUID de PISO 3 se leyó en RX: coincide
con el de TX, pero cada UUID pertenece al NetworkManager de su propia placa.
Se guardó `ProyectoComu-AP-RX`, UUID `7e11b736-9e9c-4c62-8892-57a7d0d142d4`,
con `Comu-RX` abierto en `192.168.60.1/24`. Se instaló y habilitó
`comu-web@lobor.service`; antes no había un servidor escuchando en 8080.
El equipo confirmó desde el teléfono conexión y HTTP después del reinicio real.
El registro contiene DHCPACK `192.168.60.177` y 58 lecturas en modo AP, todas con
HTTP 200. La recuperación de cinco minutos terminó con código 0 y volvió a PISO 3.
Flask siguió activo sin reinicios. Se guardó el certificado de ensayo y se dejó
el AP con autoconexión deshabilitada. El script `~/prueba_radio.py` y el archivo
de configuración de `~/comu-venv` conservaron sus hashes antes y después de la prueba.

## Recuperación que sobrevive al reinicio

`red_local.py` se instala como root en
`/usr/local/libexec/proyectocomu/red_local.py`. Lee `/etc/proyectocomu/red-ROL.json`.
Las unidades `comu-red-recuperar@.timer` y `.service` se instalan en
`/etc/systemd/system`. No dependen de la copia del repositorio ni de SSH.

`reiniciar` verifica el perfil abierto, Flask y la red original, crea el marcador
`/var/lib/proyectocomu/red-ROL/pendiente.json`, habilita la recuperación y comprueba
que está esperando antes de habilitar la autoconexión del AP y solicitar el reinicio.
El temporizador usa `OnActiveSec=5min`: al arrancar de nuevo cuenta otros cinco
minutos, sin depender de Internet ni de la hora del reloj.

Si no se confirma, deshabilita la autoconexión del AP y activa el UUID original.
Si la reconexión falla, el servicio reintenta cada 20 segundos. El perfil y las
credenciales originales no se editan ni se borran. La recuperación solo puede
conectarse a la red original si esa red está disponible y sus credenciales siguen
siendo válidas; una consola local es el respaldo si el sistema no llega a arrancar.

`confirmar` exige un boot distinto al de inicio, AP activo, configuración esperada
y respuesta HTTP con el rol correcto. Desarma el timer y deja AP y Flask automáticos.
Un bloqueo evita carreras con la recuperación; un servicio de recuperación que
hubiera quedado encolado comprueba el marcador antes de cambiar la red.

## Única comprobación de reinicio en TX

No repetir el ensayo anterior del AP abierto. Primero TX; no iniciar RX hasta
haber validado TX y recuperado PISO 3. En TX, todavía conectado a PISO 3:

```bash
sudo python3 /usr/local/libexec/proyectocomu/red_local.py estado tx
sudo python3 /usr/local/libexec/proyectocomu/red_local.py reiniciar tx
```

El segundo comando reinicia realmente y corta SSH. Desde el teléfono, conectar
a `Comu-TX` sin contraseña y abrir `http://192.168.50.1:8080`. Si conserva una
entrada antigua protegida para ese SSID, olvidar esa entrada y volver a conectarse.
Comprobar `/api/estado` y que las imágenes almacenadas siguen disponibles.

El procedimiento acordado es dejar vencer los **cinco minutos**, comprobar el
retorno automático a PISO 3 y revisar el registro de ese arranque. No hace falta
repetir otro ensayo del AP temporal. El observador de arranque es
`comu-red-observar@tx.service`; registra durante doce minutos en un directorio
privado con el boot ID. Se instala también `diagnostico_ap.py` en libexec y
`/etc/proyectocomu/observador-tx.env` contiene
`COMU_AP_PROFILE=ProyectoComu-AP-TX`. Este servicio se habilita antes del ensayo;
la recuperación lo deshabilita para futuros arranques, dejando terminar la captura.

Después de la recuperación, con la comprobación del teléfono ya realizada, registrar
el ensayo **sin activar el AP**:

```bash
sudo python3 /usr/local/libexec/proyectocomu/red_local.py validar tx
```

`validar` exige evidencia del observador del **arranque actual**, con el UUID final,
modo AP, dirección correcta y HTTP 200. Guarda `ensayo-validado.json` como root.
Mientras se programa transmisión/codificación, ambas Raspberry deben permanecer
en la red de desarrollo; los perfiles AP guardados mantienen autoconexión deshabilitada.

**Solo cuando el equipo pida activar definitivamente las redes**, ejecutar:

```bash
sudo python3 /usr/local/libexec/proyectocomu/red_local.py finalizar tx
```

`finalizar` exige ese certificado para el mismo UUID y comprueba de nuevo perfil y
Flask. Entonces habilita definitivamente la autoconexión y solicita el AP sin otro
reinicio ni temporizador de retorno. El certificado sobrevive a reinicios de desarrollo.
Retira la autorización sudo temporal si coincide exactamente con la regla creada
para esta migración. Antes de finalizar se conserva una copia del registro.

Alternativamente, se puede confirmar durante la ventana de cinco minutos:

Conectar la laptop al AP y, desde PowerShell:

```powershell
ssh lobo@192.168.50.1
```

En esa sesión, antes de los cinco minutos posteriores al arranque:

```bash
sudo python3 /usr/local/libexec/proyectocomu/red_local.py estado tx
sudo python3 /usr/local/libexec/proyectocomu/red_local.py confirmar tx
systemctl is-enabled comu-web@lobo.service
```

La confirmación se ejecuta solo después de comprobar la interfaz desde el teléfono.
Si vence el tiempo, volver a PISO 3 y a `ssh lobo@comu-tx.local`; la migración
puede iniciarse otra vez con `reiniciar tx`. Para volver manualmente, incluso
después de confirmar:

```bash
sudo python3 /usr/local/libexec/proyectocomu/red_local.py recuperar tx
```

## Procedimiento reproducible para RX, después de validar TX

Las siguientes instrucciones documentan la preparación realizada; no volver a
crear el perfil si ya existe. Comprobar primero en `lobor@comu-rx.local`:

```bash
hostname
cat /proc/device-tree/model
nmcli --version
nmcli -t -f NAME,UUID,TYPE,DEVICE connection show --active
sudo iw dev wlan0 info
sudo iw phy phy0 info
sudo ss -ltnp '( sport = :8080 )'
systemctl list-units --all --type=service '*comu*'
test -x "$HOME/comu-web-venv/bin/python"
```

Confirmar modelo Pi 4, modo AP y canal 11 permitidos. Verificar que la red de
recuperación está activa en **wlan0** y guardar su UUID real; no copiar el de TX.
Si está por Ethernet u otra interfaz, adaptar la recuperación a ese estado antes
de instalar. Confirmar rutas de proyecto/venv y cómo se ejecuta Flask, para no
duplicarlo. Instalar dependencias web separadas del entorno de pyRF24 si faltan.

Copiar únicamente las herramientas y plantillas nuevas; conservar cualquier
versión remota distinta antes de reemplazarla. Instalar los mismos cuatro archivos
systemd (incluido el observador) y `red_local.py` en las rutas anteriores. La plantilla web existente se
revisa antes de reemplazarla; la instancia de RX es `comu-web@lobor.service`.
El archivo `/etc/proyectocomu/web-lobor.env` contiene `COMU_ROLE=rx`.

Crear un perfil nuevo sin activarlo, tras comprobar que no existe ya:

```bash
sudo nmcli connection add save yes type wifi ifname wlan0 \
  con-name ProyectoComu-AP-RX ssid Comu-RX \
  connection.autoconnect no connection.autoconnect-priority 999 \
  802-11-wireless.mode ap 802-11-wireless.band bg \
  802-11-wireless.channel 11 ipv4.method shared \
  ipv4.addresses 192.168.60.1/24 ipv6.method disabled
```

Guardar como root, modo 600, `/etc/proyectocomu/red-rx.json`, con los UUID reales:

```json
{
  "role": "rx",
  "user": "lobor",
  "interface": "wlan0",
  "channel": 11,
  "address": "192.168.60.1/24",
  "ap_uuid": "UUID_REAL_DEL_NUEVO_PERFIL_RX",
  "recovery_uuid": "UUID_REAL_DEL_WIFI_ANTERIOR_RX"
}
```

Los marcadores son documentación, no un archivo ejecutable válido. El controlador
valida ambos UUID y rechaza que coincidan. No instalar este ejemplo literalmente.

Validar las instancias reales, no la instancia ficticia usada por systemd al
comprobar solamente un nombre de plantilla:

```bash
sudo systemd-analyze verify comu-web@lobor.service \
  comu-red-recuperar@rx.service comu-red-recuperar@rx.timer
sudo systemctl daemon-reload
```

Tras detener únicamente el servidor web anterior identificado, habilitar
`comu-web@lobor.service` y comprobar HTTP 200 con `rol=rx` en la red original.
Después usar los mismos comandos del procedimiento TX cambiando `tx` por `rx`,
SSID por `Comu-RX`, IP por `192.168.60.1` y usuario SSH por `lobor`.
En aquella etapa la interfaz RX informaba recepción de radio no integrada: no era un fallo
de Wi-Fi ni debe reemplazarse con resultados ficticios.

## Cierre y verificaciones

En cada placa: ensayo de AP tras reinicio validado desde teléfono, retorno comprobado
y servicio web habilitado/activo. **Dejar PISO 3 activo y AP con autoconexión deshabilitada
hasta que el equipo solicite el cambio definitivo.** Conservar perfiles,
herramientas y el JSON para retorno manual. No habilitar los scripts de pruebas de
radio como parte de esta migración. Retirar al terminar la autorización sudo
temporal amplia de soporte si se utilizó. Para conservar la posibilidad de activar
las redes más adelante se limita `/etc/sudoers.d/proyectocomu-temporal` a ejecutar
`/usr/bin/python3 /usr/local/libexec/proyectocomu/red_local.py` con sus subcomandos;
no permite comandos administrativos arbitrarios. `finalizar` retira esa regla
cuando se solicita activar definitivamente cada AP. El acceso SSH por llave se conserva.

Pruebas del controlador (Linux, no utilizan radios ni redes reales):

```bash
python3 -m unittest integracion.web.test_red_local -v
```

Fuentes: [NetworkManager: perfiles y prioridades](https://networkmanager.dev/docs/api/latest/nm-settings-nmcli.html),
[systemd: temporizadores](https://www.freedesktop.org/software/systemd/man/latest/systemd.timer.html).
