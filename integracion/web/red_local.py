"""Migración de AP abiertos. Solo se ejecuta explícitamente como root en cada Pi.

La preparación de perfiles/unidades se describe en RED_LOCAL.md. No usa radio,
GPIO, claves Wi-Fi ni comunicación con la otra Raspberry.
"""
import argparse
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.request
import uuid

CONFIG = Path('/etc/proyectocomu')
STATE = Path('/var/lib/proyectocomu')
BOOT = Path('/proc/sys/kernel/random/boot_id')
GRANT = Path('/etc/sudoers.d/proyectocomu-temporal')


def run(*args, check=True):
    result = subprocess.run(args, capture_output=True, text=True, timeout=85)
    if check and result.returncode:
        raise RuntimeError(f'Falló {args[0]} (código {result.returncode}); no se modificará otra red.')
    return result.stdout.strip()


def active(interface):
    rows = run('nmcli', '-t', '-f', 'UUID,DEVICE', 'connection', 'show', '--active')
    return next((row.split(':')[0] for row in rows.splitlines()
                 if row.endswith(':' + interface)), None)


def property_value(profile, field):
    return run('nmcli', '-g', field, 'connection', 'show', 'uuid', profile)


def health(role):
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open('http://127.0.0.1:8080/api/estado', timeout=4) as response:
        if response.status != 200 or json.load(response).get('rol') != role:
            raise RuntimeError('Flask no responde con el rol esperado.')


def unit(role, suffix):
    return f'comu-red-recuperar@{role}.{suffix}'


def validate(config, role):
    if config['role'] != role or run('hostname') != f'comu-{role}':
        raise RuntimeError('El rol no corresponde a esta Raspberry.')
    for field in ('ap_uuid', 'recovery_uuid'):
        uuid.UUID(config[field])
    if config['ap_uuid'] == config['recovery_uuid']:
        raise RuntimeError('AP y recuperación deben ser perfiles distintos.')


def check_ap(config):
    expected = {'connection.id': f'ProyectoComu-AP-{config["role"].upper()}',
                '802-11-wireless.ssid': f'Comu-{config["role"].upper()}',
                '802-11-wireless.mode': 'ap', '802-11-wireless.band': 'bg',
                '802-11-wireless.channel': str(config['channel']),
                'ipv4.method': 'shared', 'ipv4.addresses': config['address'],
                '802-11-wireless-security.key-mgmt': ''}
    for name, value in expected.items():
        if property_value(config['ap_uuid'], name) != value:
            raise RuntimeError(f'El perfil AP no coincide en {name}.')


def boot_evidence(config, directory):
    """Exige evidencia del observador root del arranque actual, no un ensayo viejo."""
    # El especificador systemd %b usa el UUID sin guiones.
    capture = directory / ('observacion-' + BOOT.read_text().strip().replace('-', '')) / 'estado.jsonl'
    records = []
    for line in capture.read_text().splitlines():
        try:
            records.append(json.loads(line))
        except ValueError:
            continue  # El observador podría estar escribiendo la última línea.
    expected_ip = config['address'].split('/')[0]
    profile_ok = any(r.get('perfil', {}).get('connection.uuid') == config['ap_uuid']
                     for r in records)
    ap_ok = any(r.get('tipo') == 'AP' and r.get('http_local') == 200 and
                any(a.get('local') == expected_ip for a in r.get('direcciones', []))
                for r in records)
    if not profile_ok or not ap_ok:
        raise RuntimeError('Falta evidencia de AP y HTTP correctos en este arranque.')


def act(action, role, pending_only=False):
    config = json.loads((CONFIG / f'red-{role}.json').read_text())
    validate(config, role)
    directory = STATE / f'red-{role}'
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    pending = directory / 'pendiente.json'
    timer = unit(role, 'timer')
    if action == 'estado':
        print(json.dumps({'configuracion': config, 'uuid_activo': active(config['interface']),
                          'pendiente': pending.exists(), 'boot_id': BOOT.read_text().strip(),
                          'temporizador': run('systemctl', 'show', timer,
                                              '-p', 'SubState', '-p', 'UnitFileState')}, indent=2))
        return
    if action == 'recuperar':
        if pending_only and not pending.exists():
            return
        run('nmcli', 'connection', 'modify', 'uuid', config['ap_uuid'],
            'connection.autoconnect', 'no')
        run('nmcli', '--wait', '60', 'connection', 'up', 'uuid',
            config['recovery_uuid'], 'ifname', config['interface'])
        if active(config['interface']) != config['recovery_uuid']:
            raise RuntimeError('La conexión original todavía no está activa.')
        pending.unlink(missing_ok=True)
        # No detener el servicio desde sí mismo: puede estar ejecutado por el timer.
        run('systemctl', 'disable', timer)
        run('systemctl', 'disable', f'comu-red-observar@{role}.service', check=False)
        print('Recuperada la red original; autoconexión del AP deshabilitada.')
        return
    check_ap(config)
    health(role)
    web = f'comu-web@{config["user"]}.service'
    if run('systemctl', 'is-enabled', web) != 'enabled':
        raise RuntimeError('Falta habilitar el servidor web permanente.')
    if action in {'validar', 'finalizar'}:
        if pending.exists() or active(config['interface']) != config['recovery_uuid']:
            raise RuntimeError('Primero debe terminar el ensayo y recuperarse la red original.')
        certificate = directory / 'ensayo-validado.json'
        if action == 'validar':
            boot_evidence(config, directory)
            certificate.write_text(json.dumps({'boot_id': BOOT.read_text().strip(),
                                               'ap_uuid': config['ap_uuid']}))
            print('Ensayo validado; AP permanece deshabilitado y se conserva la red de desarrollo.')
            return
        if json.loads(certificate.read_text()).get('ap_uuid') != config['ap_uuid']:
            raise RuntimeError('Falta validar el ensayo del perfil definitivo.')
        run('systemctl', 'disable', '--now', timer)
        run('systemctl', 'disable', f'comu-red-observar@{role}.service', check=False)
        run('nmcli', 'connection', 'modify', 'uuid', config['ap_uuid'],
            'connection.autoconnect', 'yes', 'connection.autoconnect-priority', '999')
        (directory / 'confirmado.json').write_text(json.dumps(
            {'boot_id': BOOT.read_text().strip(), 'ap_uuid': config['ap_uuid']}))
        # Retirar solo la autorización temporal exacta creada para esta migración.
        grant = GRANT
        expected = {f'{config["user"]} ALL=(ALL:ALL) NOPASSWD: ALL',
                    f'{config["user"]} ALL=(root) NOPASSWD: /usr/bin/python3 /usr/local/libexec/proyectocomu/red_local.py *'}
        if grant.exists() and grant.read_text().strip() in expected:
            grant.unlink()
        run('systemd-run', '--unit=comu-red-final-' + role + '-' + uuid.uuid4().hex[:8],
            '--collect', '--property=Type=exec', '/usr/bin/nmcli', '--wait', '45',
            'connection', 'up', 'uuid', config['ap_uuid'], 'ifname', config['interface'])
        print('AP definitivo solicitado; sin retorno automático a la red original.')
        return
    if action == 'confirmar':
        previous = json.loads(pending.read_text())
        if previous['boot_id'] == BOOT.read_text().strip():
            raise RuntimeError('Primero hay que comprobar el AP después de reiniciar.')
        if active(config['interface']) != config['ap_uuid']:
            raise RuntimeError('El AP final no está activo.')
        run('systemctl', 'disable', '--now', timer)
        run('systemctl', 'disable', f'comu-red-observar@{role}.service', check=False)
        pending.unlink()
        (directory / 'confirmado.json').write_text(json.dumps(
            {'boot_id': BOOT.read_text().strip(), 'ap_uuid': config['ap_uuid']}))
        print('Migración confirmada después del reinicio. AP y Flask quedan automáticos.')
        return
    if pending.exists():
        raise RuntimeError('Ya hay una migración pendiente; confirmar o recuperar primero.')
    if active(config['interface']) != config['recovery_uuid']:
        raise RuntimeError('Antes de migrar hay que estar conectado a la red de recuperación.')
    # No competir con temporizadores de ensayos anteriores.
    timers = run('systemctl', 'list-units', '--type=timer', '--state=active',
                 '--no-legend', '--plain')
    for line in timers.splitlines():
        other = line.split()[0]
        if other.startswith('comu-') and other != timer and run(
                'systemctl', 'show', other, '-p', 'SubState', '--value') == 'waiting':
            raise RuntimeError(f'Hay otra recuperación pendiente: {other}')
    pending.write_text(json.dumps({'boot_id': BOOT.read_text().strip()}))
    os.chmod(pending, 0o600)
    run('systemctl', 'enable', timer)
    run('systemctl', 'restart', timer)
    if run('systemctl', 'show', timer, '-p', 'SubState', '--value') != 'waiting':
        raise RuntimeError('La recuperación no quedó programada; AP no activado.')
    run('nmcli', 'connection', 'modify', 'uuid', config['ap_uuid'],
        'connection.autoconnect', 'yes', 'connection.autoconnect-priority', '999')
    if action == 'reiniciar':
        # El perfil ya probado arranca directamente al volver a encender.
        # El timer instalado también volverá a arrancar y contará cinco minutos.
        run('systemctl', 'reboot')
        return
    # PID 1 realiza el cambio aunque se corte la conexión SSH.
    run('systemd-run', '--unit=comu-red-activar-' + role + '-' + uuid.uuid4().hex[:8],
        '--collect', '--property=Type=exec', '/usr/bin/nmcli', '--wait', '45',
        'connection', 'up', 'uuid', config['ap_uuid'], 'ifname', config['interface'])
    print('Activación solicitada. Recuperación en 5 minutos, también después de reiniciar.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('estado', 'activar', 'reiniciar', 'confirmar', 'validar', 'finalizar', 'recuperar'))
    parser.add_argument('role', choices=('tx', 'rx'))
    parser.add_argument('--solo-pendiente', action='store_true')
    args = parser.parse_args()
    if os.geteuid() != 0:
        parser.error('Ejecutar mediante sudo en la Raspberry correspondiente.')
    os.umask(0o077)
    try:
        # Evita que confirmar y recuperar cambien la red simultáneamente.
        with open(f'/run/lock/comu-red-{args.role}.lock', 'a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            act(args.action, args.role, args.solo_pendiente)
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError) as exc:
        print(f'Migración detenida: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
