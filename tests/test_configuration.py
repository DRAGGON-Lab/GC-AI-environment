"""Daemon-independent tests of the rendered deployment contract."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import unittest
import tempfile
import stat

ROOT = Path(__file__).resolve().parents[1]


class ConfigurationTests(unittest.TestCase):
    def render(self, filename):
        env = dict(os.environ,
                   GCAI_BACKEND_IMAGE='example/backend@sha256:' + '0' * 64,
                   GCAI_FRONTEND_IMAGE='example/frontend@sha256:' + '0' * 64,
                   GCAI_MYSQL_IMAGE='mysql:8.4@sha256:' + '0' * 64,
                   GCAI_TRUSTED_ORIGINS='https://example.test')
        result = subprocess.run(['docker', 'compose', '-f', filename, 'config', '--format', 'json'],
                                cwd=ROOT, env=env, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)

    def test_hosted_only_tls_proxy_published_and_private_dependencies(self):
        config = self.render('compose.hosted.yml')
        for name, service in config['services'].items():
            if name != 'proxy':
                self.assertFalse(service.get('ports'), name)
        self.assertEqual([p['published'] for p in config['services']['proxy']['ports']], ['443'])
        self.assertTrue(config['networks']['application']['internal'])
        self.assertTrue(config['networks']['registry']['internal'])
        backend = config['services']['backend']
        self.assertEqual(backend['environment']['DB_USER'], 'gcai')
        self.assertNotIn('DB_PASSWORD', backend['environment'])
        self.assertIn('--workers=1', backend['command'])
        self.assertIn('--threads=4', backend['command'])
        self.assertNotIn('--preload', backend['command'])
        self.assertTrue(backend['read_only'])
        self.assertEqual(backend['user'], '10001:10001')
        janitor = config['services']['janitor']
        self.assertEqual(janitor['network_mode'], 'none')
        self.assertIn('sleep 3600', janitor['command'][0])
        self.assertEqual(janitor['volumes'][0]['source'], backend['volumes'][0]['source'])
        self.assertEqual(config['services']['db']['environment']['MYSQL_ROOT_PASSWORD_FILE'],
                         '/run/gcai/db_root_password')

    def test_secret_consumers_get_narrow_readonly_private_volumes(self):
        config = self.render('compose.hosted.yml')
        for name, expected in [('backend', 'backend-secrets'), ('db', 'mysql-secrets'), ('proxy', 'proxy-secrets')]:
            service = config['services'][name]
            self.assertFalse(service.get('secrets'), name)
            self.assertEqual(service['depends_on']['secret-init']['condition'], 'service_completed_successfully')
            mount = next(v for v in service['volumes'] if v['target'] == '/run/gcai')
            self.assertEqual(mount['source'], expected)
            self.assertTrue(mount['read_only'])
        self.assertEqual(config['services']['db']['environment']['MYSQL_ROOT_HOST'], 'localhost')
        for script in ['10-import-registry.sh', '20-create-app-user.sh']:
            self.assertFalse((ROOT / 'scripts' / script).stat().st_mode & 0o111)

    def test_prepared_secret_mode_and_rotation(self):
        spec = importlib.util.spec_from_file_location('prepare_secrets', ROOT / 'scripts/prepare-secrets.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / 'source'
            target = Path(temporary) / 'consumer/secret'
            source.write_bytes(b'first-private-value')
            source.chmod(0o600)
            module.prepare(source, target, os.getuid(), os.getgid())
            self.assertEqual(target.read_bytes(), source.read_bytes())
            self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o400)
            self.assertEqual(stat.S_IMODE(target.parent.stat().st_mode), 0o700)
            source.write_bytes(b'rotated-private-value')
            module.prepare(source, target, os.getuid(), os.getgid())
            self.assertEqual(target.read_bytes(), source.read_bytes())
            self.assertEqual(list(target.parent.iterdir()), [target])

    def test_local_ports_are_loopback_only(self):
        config = self.render('docker-compose.yml')
        ports = [p for service in config['services'].values() for p in service.get('ports', [])]
        self.assertEqual(len(ports), 1)
        self.assertEqual(ports[0]['host_ip'], '127.0.0.1')

    def test_authentication_covers_frontend_and_api(self):
        config = (ROOT / 'nginx/hosted.conf').read_text()
        self.assertIn("auth_basic 'GC-AI workspace';", config)
        self.assertIn('auth_basic_user_file /run/gcai/proxy_htpasswd;', config)
        self.assertNotIn('auth_basic off', config)
        self.assertIn('proxy_read_timeout 180s;', config)
        self.assertIn('limit_conn api_connections 4;', config)
        self.assertIn('server_name _;', config)
        self.assertIn('ssl_protocols TLSv1.2 TLSv1.3;', config)
        self.assertIn("proxy_set_header Authorization '';", config)
        self.assertIn('access_log off;', config)

    def test_importer_requires_digest_and_never_starts_checkpoint(self):
        spec = importlib.util.spec_from_file_location('import_assets', ROOT / 'scripts/import-assets.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(module.pinned('example@sha256:' + 'a' * 64), 'example@sha256:' + 'a' * 64)
        for ref in ['example:latest', 'example', 'example@sha256:short']:
            with self.assertRaises(Exception):
                module.pinned(ref)
        source = (ROOT / 'scripts/import-assets.py').read_text()
        self.assertIn("run('start', database", source)
        self.assertNotIn("run('start', checkpoint", source)
        self.assertIn("'iGEM2024', 'parts'", source)


if __name__ == '__main__':
    unittest.main()
