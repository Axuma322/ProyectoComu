"""Pruebas de recuperación con comandos simulados; no cambian redes ni servicios."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from . import red_local as red


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.boot = root / 'boot'
        self.boot.write_text('boot-actual')
        self.config = {'role': 'tx', 'user': 'lobo', 'interface': 'wlan0',
                       'ap_uuid': '11111111-1111-4111-8111-111111111111',
                       'recovery_uuid': '22222222-2222-4222-8222-222222222222',
                       'channel': 1, 'address': '192.168.50.1/24'}
        (root / 'red-tx.json').write_text(json.dumps(self.config))
        self.directory = root / 'red-tx'
        self.directory.mkdir()
        self.pending = self.directory / 'pendiente.json'
        self.pending.write_text(json.dumps({'boot_id': 'boot-anterior'}))
        for name, value in [('CONFIG', root), ('STATE', root), ('BOOT', self.boot),
                            ('GRANT', root / 'sudo-temporal')]:
            p = patch.object(red, name, value)
            p.start()
            self.addCleanup(p.stop)
        for name in ('check_ap', 'health'):
            p = patch.object(red, name)
            p.start()
            self.addCleanup(p.stop)
        self.active_uuid = self.config['ap_uuid']
        self.calls = []
        self.waiting = True
        self.fail_recovery = False
        p = patch.object(red, 'run', side_effect=self.command)
        p.start()
        self.addCleanup(p.stop)

    def command(self, *args, **kwargs):
        self.calls.append(args)
        if args == ('hostname',):
            return 'comu-tx'
        if args[:3] == ('systemctl', 'is-enabled', 'comu-web@lobo.service'):
            return 'enabled'
        if args[:5] == ('nmcli', '-t', '-f', 'UUID,DEVICE', 'connection'):
            return self.active_uuid + ':wlan0'
        if args[:3] == ('systemctl', 'show', 'comu-red-recuperar@tx.timer'):
            return 'waiting' if self.waiting else 'inactive'
        if args[:5] == ('nmcli', '--wait', '60', 'connection', 'up'):
            if self.fail_recovery:
                raise RuntimeError('Red original no disponible')
            self.active_uuid = self.config['recovery_uuid']
        return ''

    def test_no_confirmation_without_reboot(self):
        self.pending.write_text(json.dumps({'boot_id': 'boot-actual'}))
        with self.assertRaisesRegex(RuntimeError, 'reiniciar'):
            red.act('confirmar', 'tx')
        self.assertTrue(self.pending.exists())
        self.assertFalse(any(c[:2] == ('systemctl', 'disable') for c in self.calls))

    def test_confirmation_requires_final_ap(self):
        self.active_uuid = self.config['recovery_uuid']
        with self.assertRaisesRegex(RuntimeError, 'no está activo'):
            red.act('confirmar', 'tx')
        self.assertTrue(self.pending.exists())

    def test_confirmation_disarms_guard_after_reboot(self):
        red.act('confirmar', 'tx')
        self.assertFalse(self.pending.exists())
        self.assertTrue((self.directory / 'confirmado.json').exists())
        self.assertIn(('systemctl', 'disable', '--now', 'comu-red-recuperar@tx.timer'), self.calls)

    def test_queued_guard_cannot_revert_confirmed_migration(self):
        self.pending.unlink()
        red.act('recuperar', 'tx', pending_only=True)
        self.assertFalse(any(c[0] == 'nmcli' for c in self.calls))

    def test_failed_guard_prevents_ap_activation(self):
        self.pending.unlink()
        self.active_uuid = self.config['recovery_uuid']
        self.waiting = False
        with self.assertRaisesRegex(RuntimeError, 'no quedó programada'):
            red.act('activar', 'tx')
        self.assertFalse(any(c[0] == 'systemd-run' for c in self.calls))
        self.assertFalse(any(c[:3] == ('nmcli', 'connection', 'modify') for c in self.calls))

    def test_failed_return_keeps_pending_for_retry(self):
        self.fail_recovery = True
        with self.assertRaisesRegex(RuntimeError, 'no disponible'):
            red.act('recuperar', 'tx', pending_only=True)
        self.assertTrue(self.pending.exists())
        self.assertIn(('nmcli', 'connection', 'modify', 'uuid', self.config['ap_uuid'],
                       'connection.autoconnect', 'no'), self.calls)

    def test_direct_reboot_is_guarded_without_intermediate_ap_switch(self):
        self.pending.unlink()
        self.active_uuid = self.config['recovery_uuid']
        red.act('reiniciar', 'tx')
        self.assertTrue(self.pending.exists())
        self.assertIn(('systemctl', 'enable', 'comu-red-recuperar@tx.timer'), self.calls)
        self.assertIn(('systemctl', 'reboot'), self.calls)
        self.assertFalse(any(c[0] == 'systemd-run' for c in self.calls))
        self.assertLess(self.calls.index(('systemctl', 'restart', 'comu-red-recuperar@tx.timer')),
                        self.calls.index(('systemctl', 'reboot')))

    def test_evidence_rejects_previous_boot(self):
        old = self.directory / 'observacion-bootanterior'
        old.mkdir()
        (old / 'estado.jsonl').write_text('{}\n')
        with self.assertRaises(FileNotFoundError):
            red.boot_evidence(self.config, self.directory)

    def test_evidence_requires_http_on_ap_with_correct_address(self):
        directory = self.directory / 'observacion-bootactual'
        directory.mkdir()
        capture = directory / 'estado.jsonl'
        records = [{'perfil': {'connection.uuid': self.config['ap_uuid']}},
                   {'tipo': 'AP', 'http_local': None,
                    'direcciones': [{'local': '192.168.50.1'}]}]
        capture.write_text('\n'.join(json.dumps(r) for r in records))
        with self.assertRaisesRegex(RuntimeError, 'Falta evidencia'):
            red.boot_evidence(self.config, self.directory)
        records[1]['http_local'] = 200
        capture.write_text('\n'.join(json.dumps(r) for r in records))
        red.boot_evidence(self.config, self.directory)

    def test_finalization_requires_validated_certificate(self):
        self.pending.unlink()
        self.active_uuid = self.config['recovery_uuid']
        with self.assertRaises(FileNotFoundError):
            red.act('finalizar', 'tx')
        self.assertFalse(any(c[0] == 'systemd-run' for c in self.calls))

    def test_finalization_after_successful_boot_removes_only_own_sudo_grant(self):
        self.pending.unlink()
        self.active_uuid = self.config['recovery_uuid']
        red.GRANT.write_text('lobo ALL=(ALL:ALL) NOPASSWD: ALL\n')
        (self.directory / 'ensayo-validado.json').write_text(json.dumps(
            {'boot_id': 'boot-anterior', 'ap_uuid': self.config['ap_uuid']}))
        red.act('finalizar', 'tx')
        self.assertFalse(red.GRANT.exists())
        self.assertTrue((self.directory / 'confirmado.json').exists())
        self.assertTrue(any(c[0] == 'systemd-run' for c in self.calls))
        self.assertFalse(any(c[:2] == ('systemctl', 'reboot') for c in self.calls))

    def test_validation_keeps_development_wifi_and_ap_disabled(self):
        self.pending.unlink()
        self.active_uuid = self.config['recovery_uuid']
        with patch.object(red, 'boot_evidence'):
            red.act('validar', 'tx')
        self.assertTrue((self.directory / 'ensayo-validado.json').exists())
        self.assertFalse(any(c[0] in {'nmcli', 'systemd-run'} and
                             (c[0] == 'systemd-run' or 'modify' in c) for c in self.calls))


if __name__ == '__main__':
    unittest.main()
