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
radio ni GPIO. Mantener la terminal abierta durante la prueba. Desde Android en
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
