#!/usr/bin/env python3
"""Copy mounted operator inputs into private volumes owned by their consumers."""
import os
import hashlib
import hmac
import re
from pathlib import Path
import shutil
import tempfile


def prepare(source, destination, uid, gid, expected_sha256=None):
    source, destination = Path(source), Path(destination)
    destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chown(str(destination.parent), uid, gid)
    os.chmod(str(destination.parent), 0o700)
    fd, temporary = tempfile.mkstemp(prefix='.prepare-', dir=str(destination.parent))
    try:
        with os.fdopen(fd, 'wb') as output, source.open('rb') as incoming:
            if expected_sha256 is None:
                shutil.copyfileobj(incoming, output)
            else:
                if not re.fullmatch('[0-9a-f]{64}', expected_sha256):
                    raise ValueError('Expected asset identity must be a lowercase SHA256')
                digest = hashlib.sha256()
                while chunk := incoming.read(1024 * 1024):
                    digest.update(chunk)
                    output.write(chunk)
                if not hmac.compare_digest(digest.hexdigest(), expected_sha256):
                    raise ValueError('Provisioned asset does not match its release manifest')
            output.flush()
            os.fsync(output.fileno())
            os.fchown(output.fileno(), uid, gid)
            os.fchmod(output.fileno(), 0o400)
        os.replace(temporary, str(destination))
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main():
    consumers = {
        'backend': (int(os.getenv('GCAI_UID', '10001')), int(os.getenv('GCAI_GID', '10001'))),
        'mysql': (int(os.getenv('GCAI_MYSQL_UID', '999')), int(os.getenv('GCAI_MYSQL_GID', '999'))),
        'mysql-init': (int(os.getenv('GCAI_MYSQL_UID', '999')), int(os.getenv('GCAI_MYSQL_GID', '999'))),
        'proxy': (int(os.getenv('GCAI_NGINX_UID', '101')), int(os.getenv('GCAI_NGINX_GID', '101'))),
    }
    for consumer, name, source in [
        ('backend', 'db_app_password', '/run/secrets/db_app_password'),
        ('backend', '160_model.pth', '/input/160_model.pth'),
        ('mysql', 'db_app_password', '/run/secrets/db_app_password'),
        ('mysql', 'db_root_password', '/run/secrets/db_root_password'),
        ('mysql', 'registry.sql', '/input/registry.sql'),
        ('mysql-init', '10-import-registry.sh', '/input/10-import-registry.sh'),
        ('mysql-init', '20-create-app-user.sh', '/input/20-create-app-user.sh'),
    ]:
        expected = None
        if name in ('160_model.pth', 'registry.sql'):
            variable = 'GCAI_EXPECTED_CHECKPOINT_SHA256' if name == '160_model.pth' else 'GCAI_EXPECTED_REGISTRY_SHA256'
            expected = os.environ[variable]
        prepare(source, '/prepared/' + consumer + '/' + name, *consumers[consumer], expected_sha256=expected)
    if os.getenv('GCAI_PREPARE_PROXY') == '1':
        for name in ('proxy_htpasswd', 'tls_certificate', 'tls_key'):
            prepare('/run/secrets/' + name, '/prepared/proxy/' + name, *consumers['proxy'])


if __name__ == '__main__':
    main()
