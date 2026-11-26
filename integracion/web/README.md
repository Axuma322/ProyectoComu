# Interfaz web local

Flask define la API y las páginas; Waitress las sirve en `0.0.0.0:8080`, sin
debug ni recargador. Cada Raspberry ejecuta su propia instancia. El navegador
usa recursos locales de `static/` y `templates/`, sin CDN.
La aplicación no importa pyRF24 ni gpiozero y no comunica las dos Raspberry
mediante HTTP. El transporte pertenece a `integracion.enlace`.

TX: `Comu-TX`, http://192.168.50.1:8080. RX: `Comu-RX`,
http://192.168.60.1:8080. La [guía de operación](../../documentacion/operacion.md)
describe servicios y uso desde teléfonos. La instalación integrada está en
[IMAGENES.md](../IMAGENES.md); copiar únicamente esta carpeta ya no basta,
pues depende de `transmision/` y del resto de integración.

## Uso

En TX: cargar o elegir una BMP/PGM gris de hasta 320 × 240 y 2 MiB; elegirla
ya la deja lista para el botón. El modo y los bits los pone el DIP (la página
los muestra en vivo) y se transmite con el botón físico; desde la web no se
puede transmitir. **Probar compresión** usa el modo del DIP y es opcional.

En RX: observar recepción, abrir imágenes guardadas y consultar sus métricas.
La galería sobrevive al reinicio. Se pueden borrar imágenes individualmente en
ambos extremos; TX bloquea el borrado durante una compresión o transmisión.

La UI consulta el estado aproximadamente cada tres segundos. El progreso viene
del proceso de enlace. El límite de 10 s de una petición HTTP no cancela el
envío de radio. No existe corte global de 60 s.

## API

| Método y ruta | Uso |
|---|---|
| `GET /api/estado` | Rol, disponibilidad del proceso, progreso, selección, compresión y última imagen |
| `GET /api/imagenes` | Catálogo de fuentes TX |
| `POST /api/imagenes` | Subida multipart, campo `imagen`, en TX |
| `DELETE /api/imagenes/<nombre>` | Borrar fuente y, si corresponde, selección y derivados TX |
| `POST /api/seleccion` | JSON con `imagen`; `modo` y `bits` son opcionales, el botón usa el DIP |
| `POST /api/codificar` | Compresión local asíncrona con modo/bits del DIP (409 sin `--gpio`); no transmite |
| `POST /api/transmitir` | Desactivada: responde 403, se transmite con el botón físico |
| `GET /api/recibidas` | Galería RX con metadatos por recepción |
| `DELETE /api/recibidas/<nombre>` | Borrar imagen y su registro RX |
| `GET /imagenes/<nombre>/vista.png` | Vista de fuente TX |
| `GET /codificada/vista.png`, `GET /codificada/archivo.bin` | Vista y descarga del resultado local TX |
| `GET /recibidas/<nombre>/vista.png` | Vista de una imagen RX |

Las operaciones de cambio usan el token de página en `X-Comu-Token`.
El resultado de cada envío se consulta en `/api/estado`, que también trae el
DIP leído (`enlace.dip`), y queda en `resultados/<trabajo>.json` en TX.
Un heartbeat reciente acredita el proceso local, sin probar que RX esté encendida
ni que una imagen se haya entregado.

## Ejecución y dependencias

Servicios instalados: `comu-web@lobo.service` en TX y
`comu-web@lobor.service` en RX. Antes de iniciar un servidor manual, detener
la instancia web de ese equipo para no duplicar el puerto:

```bash
cd ~/ProyectoComu
sudo systemctl stop "comu-web@$(id -un).service"
~/comu-web-venv/bin/python -m integracion.web --role tx
# En RX usar --role rx. Terminar con Ctrl+C y restaurar el servicio:
sudo systemctl start "comu-web@$(id -un).service"
```

Se usa Python 3.13 en las placas comprobadas. `requirements.txt` declara Flask,
Waitress, Pillow y NumPy. `~/comu-web-venv` está separado de `~/comu-venv`, que
conserva pyRF24. `libopenblas0-pthread` quedó instalada en ambas placas.
La instalación puede necesitar Internet; la operación no lo necesita.

Datos: `~/.local/share/proyectocomu-web`, fuera del repositorio. `--data-dir`
permite otra ubicación en pruebas. Ver el [mapa de almacenamiento](../../documentacion/arquitectura_software.md#almacenamiento-local).
PNG es una vista web; no reemplaza el original ni el flujo de radio.

## Diagnóstico y pruebas

```bash
curl --connect-timeout 3 -fsS http://127.0.0.1:8080/api/estado
~/comu-web-venv/bin/python -m unittest integracion.web.test_web -v
```

`diagnostico_ap.py` genera `eventos.jsonl` y `estado.jsonl` mediante campos
permitidos, sin guardar claves Wi-Fi. No activa AP. Las propuestas anteriores
se conservaron en [diagnóstico WPA2](../../documentacion/despliegue/antecedentes_ap_wpa2.md).
La red vigente es abierta. [RED_LOCAL.md](RED_LOCAL.md) documenta la migración;
[redes_definitivas.md](../../documentacion/despliegue/redes_definitivas.md),
la operación permanente y la recuperación manual.
