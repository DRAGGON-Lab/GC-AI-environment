#!/usr/bin/env python3
"""Import a verified checkpoint layer and inspect subsequent overlays; never run the image."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import tarfile
import tempfile
import urllib.request


def sha256(value):
    if not re.fullmatch('sha256:[0-9a-f]{64}', value):
        raise ValueError('Expected an immutable SHA256 descriptor')
    return value


def verified_bytes(content, expected):
    if 'sha256:' + hashlib.sha256(content).hexdigest() != sha256(expected):
        raise ValueError('Registry manifest integrity failure')
    return json.loads(content)


class DockerHub:
    def __init__(self, repository):
        if not re.fullmatch('[a-z0-9_.-]+/[a-z0-9_.-]+', repository):
            raise ValueError('Use a Docker Hub owner/repository name')
        self.repository = repository
        url = 'https://auth.docker.io/token?service=registry.docker.io&scope=repository:' + repository + ':pull'
        with urllib.request.urlopen(url, timeout=30) as response:
            self.token = json.load(response)['token']

    def fetch(self, kind, identity):
        url = 'https://registry-1.docker.io/v2/' + self.repository + '/' + kind + '/' + sha256(identity)
        return urllib.request.urlopen(urllib.request.Request(url, headers={
            'Authorization': 'Bearer ' + self.token,
            'Accept': 'application/vnd.docker.distribution.manifest.v2+json,application/vnd.oci.image.manifest.v1+json,application/vnd.oci.image.index.v1+json,application/vnd.docker.distribution.manifest.list.v2+json',
        }), timeout=60)


def import_layer(fetch, manifest_digest, layer_digest, member_name, expected_checkpoint, output):
    member_name = member_name.lstrip('/')
    target = PurePosixPath(member_name)
    if '..' in target.parts or not target.parts:
        raise ValueError('Checkpoint path must be a normalized image path')
    with fetch('manifests', manifest_digest) as source:
        manifest = verified_bytes(source.read(), manifest_digest)
    if 'manifests' in manifest:
        candidates = [item for item in manifest['manifests'] if item.get('platform', {}).get('os') == 'linux' and item.get('platform', {}).get('architecture') == 'amd64']
        if len(candidates) != 1:
            raise ValueError('Expected one Linux/amd64 image manifest')
        with fetch('manifests', candidates[0]['digest']) as source:
            manifest = verified_bytes(source.read(), candidates[0]['digest'])
    layers = [layer['digest'] for layer in manifest['layers']]
    if layers.count(layer_digest) != 1:
        raise ValueError('Checkpoint layer is not uniquely identified by the pinned manifest')
    start = layers.index(layer_digest)
    ancestors = {str(parent) for parent in target.parents if str(parent) != '.'}
    whiteouts = {str(target.parent / ('.wh.' + target.name))}
    whiteouts |= {str(PurePosixPath(parent).parent / ('.wh.' + PurePosixPath(parent).name)) for parent in ancestors}
    whiteouts |= {str(parent / '.wh..wh..opq') for parent in target.parents}
    output = Path(output)
    if output.exists():
        raise FileExistsError('Checkpoint output already exists')
    output.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.layer-import-', dir=output.parent) as temporary:
        stage = Path(temporary)
        checkpoint = stage / 'checkpoint'
        for index, identity in enumerate(layers[start:]):
            archive_path = stage / 'layer'
            digest = hashlib.sha256()
            with fetch('blobs', identity) as source, archive_path.open('xb') as destination:
                while chunk := source.read(1024 * 1024):
                    digest.update(chunk)
                    destination.write(chunk)
            if 'sha256:' + digest.hexdigest() != identity:
                raise ValueError('Registry layer integrity failure')
            found = 0
            with tarfile.open(archive_path) as archive:
                for member in archive:
                    name = member.name
                    if name.startswith('/') or '..' in PurePosixPath(name).parts:
                        raise ValueError('Image layers must use normalized relative paths')
                    name = str(PurePosixPath(name)).rstrip('/')
                    if index == 0 and name == member_name:
                        found += 1
                        if not member.isfile() or found != 1:
                            raise ValueError('Checkpoint must be one regular file in the source layer')
                        with archive.extractfile(member) as source, checkpoint.open('xb') as destination:
                            shutil.copyfileobj(source, destination)
                    elif index > 0 and (name == member_name or name in whiteouts or name in ancestors and not member.isdir()):
                        raise ValueError('A later image layer changes or hides the checkpoint')
            if index == 0 and found != 1:
                raise ValueError('Checkpoint was not found in the approved source layer')
            archive_path.unlink()
        with checkpoint.open('rb') as source:
            actual = hashlib.file_digest(source, 'sha256').hexdigest()
        if actual != expected_checkpoint:
            raise ValueError('Extracted checkpoint differs from the release manifest')
        checkpoint.chmod(0o600)
        # Hard-link publication refuses an existing target even if it races validation.
        os.link(checkpoint, output)
    return {'manifest_sha256': manifest_digest, 'source_layer': layer_digest,
            'verified_layers': layers[start:], 'checkpoint_sha256': actual,
            'checkpoint_bytes': output.stat().st_size, 'application_executed': False, 'checkpoint_deserialized': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', required=True, help='Docker Hub owner/repository@sha256:...')
    parser.add_argument('--layer', required=True)
    parser.add_argument('--path', required=True)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    repository, manifest = args.image.split('@', 1)
    if not re.fullmatch('[0-9a-f]{64}', args.sha256):
        parser.error('Supply the reviewed checkpoint SHA256')
    registry = DockerHub(repository)
    receipt = import_layer(registry.fetch, sha256(manifest), sha256(args.layer), args.path, args.sha256, args.output)
    with args.output.with_suffix('.receipt.json').open('x') as stream:
        json.dump(receipt, stream, indent=2)
        stream.write('\n')
