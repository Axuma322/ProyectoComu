# Redes Wi-Fi de operación de ProyectoComu

Configuración del 26 de noviembre de 2026. Cada Raspberry sirve su página y
SSH dentro de su propia red abierta. DHCP asigna la dirección del teléfono.
Las imágenes entre las Raspberry siguen pasando exclusivamente por nRF24.

| Equipo | Red abierta | Página | SSH desde esa red | Canal Wi-Fi |
|---|---|---|---|---:|
| TX, Zero W | Comu-TX | http://192.168.50.1:8080 | `ssh lobo@192.168.50.1` | 1 |
| RX, Pi 4 B | Comu-RX | http://192.168.60.1:8080 | `ssh lobor@192.168.60.1` | 11 |

No hay contraseña Wi-Fi. Las cuentas y la autenticación SSH se conservan.
Cada teléfono se conecta únicamente a la red de su Raspberry. Si aparece un
aviso de falta de Internet, permanecer conectado para usar la página local.
La operación no necesita router, Internet ni computadora central.

## Persistencia y arranque

Los perfiles persistentes son `ProyectoComu-AP-TX` y `ProyectoComu-AP-RX`,
respectivamente. `red_local.py finalizar` establece autoconexión habilitada y
prioridad 999, detiene y deshabilita el temporizador de recuperación del ensayo
y activa el perfil mediante systemd. No hay retorno automático a PISO 3.

Antes del cambio se comprobaron activos y habilitados:

| TX | RX |
|---|---|
| `comu-web@lobo.service` | `comu-web@lobor.service` |
| `comu-enlace@lobo.service` | `comu-enlace@lobor.service` |

El servidor web y el proceso de radio se inician por systemd y continúan al
cerrar SSH. La activación final aprovecha los ensayos de AP después del reinicio
que ya se habían validado en ambas placas; no exige repetir aquel ensayo de
cinco minutos. Esta activación no reinicia las Raspberry.

El equipo ya completó las [seis pruebas de imágenes en PISO 3](../pruebas/2026-11-26-tres-imagenes/README.md).
La transmisión con ambos AP simultáneamente activos, las power banks y el
alcance se comprobarán como pasos posteriores.

## Acceso para desarrollo y recuperación manual

Para entrar por SSH desde una computadora, conectarla primero a Comu-TX o
Comu-RX y usar la dirección de la tabla. Con un único adaptador Wi-Fi se accede
a una de esas redes a la vez. El cambio de red de cada Raspberry interrumpe
su sesión SSH anterior por PISO 3.

Se conservan el perfil `netplan-wlan0-PISO 3`, sus credenciales y los scripts
de recuperación. El script original `/usr/local/sbin/comu-tx-rollback` permanece
en TX. No se borran ni se reemplazan los programas de prueba de radio.

Para volver al desarrollo, **dentro del alcance de PISO 3**, entrar por SSH a
la Raspberry desde su AP y ejecutar el comando del equipo correspondiente:

```bash
# En lobo@comu-tx:
sudo python3 /usr/local/libexec/proyectocomu/red_local.py recuperar tx

# En lobor@comu-rx:
sudo python3 /usr/local/libexec/proyectocomu/red_local.py recuperar rx
```

Cada comando deshabilita la autoconexión del AP y conecta el perfil original.
La sesión se corta durante el cambio. Volver a conectar la computadora a PISO 3
y utilizar `ssh lobo@comu-tx.local` o `ssh lobor@comu-rx.local`.

Después de programar, para volver al AP permanente desde PISO 3:

```bash
# Solo en TX:
sudo python3 /usr/local/libexec/proyectocomu/red_local.py finalizar tx

# Solo en RX:
sudo python3 /usr/local/libexec/proyectocomu/red_local.py finalizar rx
```

`finalizar` retira la autorización administrativa temporal de la migración.
Los comandos posteriores con sudo requieren la autenticación habitual del
usuario en su terminal. El acceso SSH por llave permanece disponible.

## Registro de esta activación

Se verificaron los perfiles guardados, la red original activa, ausencia de
migraciones pendientes, temporizadores de ensayo deshabilitados, HTTP local
y proceso nRF24 disponible en ambos equipos. El controlador instalado coincidía
por SHA-256 con `integracion/web/red_local.py`.

Se ejecutó `finalizar tx` primero y `finalizar rx` después, tras comprobar TX
desde el teléfono. Ambos comandos terminaron con código 0 y solicitaron el AP
sin retorno automático. TX quedó comprobada desde el teléfono; la comprobación
final de RX está en curso.
