#!/bin/bash
# Aplicar únicamente después de probar el paquete en ProyectoComu-integracion.
# Instalación del paquete original; no sincroniza Git ni configura los AP.
# Para mantenimiento conservar también datos externos al checkout y los venv.
set -euo pipefail
COMU_ROLE=${1:?Uso: sudo bash instalar_imagenes.sh tx|rx}
case "$COMU_ROLE" in
  tx) COMU_USER=lobo ;;
  rx) COMU_USER=lobor ;;
  *) exit 2 ;;
esac
test "$EUID" -eq 0
test "$(hostname)" = "comu-$COMU_ROLE"
COMU_HOME=$(getent passwd "$COMU_USER" | cut -d: -f6)
COMU_PROJECT="$COMU_HOME/ProyectoComu"
COMU_SOURCE="$COMU_HOME/ProyectoComu-integracion"
COMU_PY="$COMU_HOME/comu-web-venv/bin/python"
test -d "$COMU_PROJECT"
test ! -L "$COMU_PROJECT"
test -f "$COMU_HOME/comu-integracion.tgz"
cd "$COMU_SOURCE"
runuser -u "$COMU_USER" -- "$COMU_PY" -m integracion.enlace --role "$COMU_ROLE" --check
# No hay cambios de perfiles Wi-Fi, AP ni entornos de radio en este instalador.
COMU_BACKUP="$COMU_HOME/codigo-antes-imagenes-$(date -u +%Y%m%dT%H%M%SZ)-$$.tgz"
runuser -u "$COMU_USER" -- tar -czf "$COMU_BACKUP" -C "$COMU_HOME" ProyectoComu
COMU_CHANGED=0
comu_restore() {
  COMU_RESULT=$?
  if test "$COMU_RESULT" -ne 0 && test "$COMU_CHANGED" -eq 1; then
    systemctl disable --now "comu-enlace@$COMU_USER.service" || true
    runuser -u "$COMU_USER" -- tar -xzf "$COMU_BACKUP" -C "$COMU_HOME"
    systemctl start "comu-web@$COMU_USER.service"
    printf 'Se restauró el código anterior desde %s\n' "$COMU_BACKUP" >&2
  fi
}
trap comu_restore EXIT
if test "$(systemctl show "comu-enlace@$COMU_USER.service" -p LoadState --value)" = loaded; then
  systemctl stop "comu-enlace@$COMU_USER.service"
fi
COMU_CHANGED=1
systemctl stop "comu-web@$COMU_USER.service"
runuser -u "$COMU_USER" -- tar -xzf "$COMU_HOME/comu-integracion.tgz" -C "$COMU_PROJECT"
install -m 644 "$COMU_PROJECT/integracion/web/comu-enlace@.service" /etc/systemd/system/comu-enlace@.service
systemctl daemon-reload
systemd-analyze verify "comu-enlace@$COMU_USER.service" "comu-web@$COMU_USER.service"
systemctl enable --now "comu-web@$COMU_USER.service" "comu-enlace@$COMU_USER.service"
for COMU_ATTEMPT in $(seq 1 30); do
  if runuser -u "$COMU_USER" -- "$COMU_PY" -c '
import json, sys, urllib.error, urllib.request
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
try:
    with opener.open("http://127.0.0.1:8080/api/estado",timeout=2) as r:
        d=json.load(r)
except (urllib.error.URLError, TimeoutError, OSError, ValueError):
    print("Esperando a Flask...", flush=True)
    sys.exit(1)
if not d.get("radio_integrado") or not d.get("codificacion_integrada"):
    print("Esperando al proceso de enlace...", flush=True)
    sys.exit(1)
print(json.dumps(d))
'; then
    printf 'Instalación completa. Copia anterior: %s\n' "$COMU_BACKUP"
    exit 0
  fi
  sleep 2
done
journalctl -u "comu-enlace@$COMU_USER.service" -n 20 --no-pager
printf '%s\n' 'El enlace no quedó disponible. Se conserva la copia anterior; no se cambiaron las redes.' >&2
exit 1
