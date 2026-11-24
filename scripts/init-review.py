#!/usr/bin/env python3
"""Create new private local-review credentials and a localhost-only TLS certificate."""
import argparse
import os
from pathlib import Path
import secrets
import subprocess


def initialize(root):
    root.mkdir(mode=0o700, parents=True, exist_ok=False)
    for name in ('db_root_password', 'db_app_password', 'workspace_password'):
        with open(root / name, 'x', opener=lambda path, flags: os.open(path, flags, 0o600)) as stream:
            stream.write(secrets.token_hex(32))
    password = (root / 'workspace_password').read_text()
    hashed = subprocess.run(['openssl', 'passwd', '-6', '-stdin'], input=password, text=True,
                            capture_output=True, check=True).stdout.strip()
    with open(root / 'htpasswd', 'x', opener=lambda path, flags: os.open(path, flags, 0o600)) as stream:
        stream.write('review:' + hashed + '\n')
    subprocess.run(['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes',
                    '-keyout', str(root / 'tls.key'), '-out', str(root / 'tls.crt'),
                    '-days', '7', '-subj', '/CN=localhost', '-addext', 'subjectAltName=DNS:localhost'],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for name in ('tls.key', 'tls.crt'):
        (root / name).chmod(0o600)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=Path('secrets'))
    args = parser.parse_args()
    initialize(args.directory)
    print('Private review inputs created. Username: review. Read the workspace_password file privately.')


if __name__ == '__main__':
    main()
