"""Layer import and provisioning reject altered bytes without running legacy apps."""
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


layer_import = load('layer_import', ROOT / 'scripts/import-checkpoint.py')
prepare = load('prepare_integrity', ROOT / 'scripts/prepare-secrets.py')


def identity(content):
    return 'sha256:' + hashlib.sha256(content).hexdigest()


def layer(files):
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode='w:gz') as archive:
        for name, content in files.items():
            member = tarfile.TarInfo(name)
            member.size = len(content)
            archive.addfile(member, io.BytesIO(content))
    return buffer.getvalue()


class IntegrityTests(unittest.TestCase):
    def test_source_and_later_layer_hashes_and_overlays_are_verified(self):
        target = 'app/model.pth'
        for mutation in [None, 'target', 'whiteout', 'opaque', 'layer-bytes', 'checkpoint-hash', 'alias-overlay']:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                content = b'approved checkpoint'
                original = layer({target: content})
                later = layer({'unchanged.txt': b'not the checkpoint'})
                if mutation == 'alias-overlay': later = layer({'././app/model.pth': b'tampered'})
                if mutation == 'target': later = layer({target: b'tampered'})
                if mutation == 'whiteout': later = layer({'app/.wh.model.pth': b''})
                if mutation == 'opaque': later = layer({'app/.wh..wh..opq': b''})
                # An omitted earlier layer is deliberately unavailable: no full image pull.
                manifest = json.dumps({'layers': [{'digest': 'sha256:'+'0'*64}, {'digest': identity(original)}, {'digest': identity(later)}]}).encode()
                blobs = {identity(manifest): manifest, identity(original): original, identity(later): later}
                if mutation == 'layer-bytes': blobs[identity(later)] = b'corrupt archive bytes'
                calls = []
                def fetch(kind, descriptor):
                    calls.append(descriptor)
                    return io.BytesIO(blobs[descriptor])
                output = Path(directory) / 'model.pth'
                expected = hashlib.sha256(content).hexdigest() if mutation != 'checkpoint-hash' else '0'*64
                if mutation:
                    with self.assertRaises(ValueError):
                        layer_import.import_layer(fetch, identity(manifest), identity(original), target, expected, output)
                    self.assertFalse(output.exists())
                else:
                    receipt = layer_import.import_layer(fetch, identity(manifest), identity(original), target, expected, output)
                    self.assertEqual(output.read_bytes(), content)
                    self.assertFalse(receipt['checkpoint_deserialized'])
                    self.assertEqual(calls, [identity(manifest), identity(original), identity(later)])

    def test_provisioning_rejects_tampering_before_replacing_existing_asset(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'source'
            destination = Path(directory) / 'private/model.pth'
            source.write_bytes(b'approved')
            expected = hashlib.sha256(source.read_bytes()).hexdigest()
            prepare.prepare(source, destination, os.getuid(), os.getgid(), expected)
            source.write_bytes(b'tampered')
            with self.assertRaises(ValueError):
                prepare.prepare(source, destination, os.getuid(), os.getgid(), expected)
            self.assertEqual(destination.read_bytes(), b'approved')
            self.assertEqual(list(destination.parent.iterdir()), [destination])
