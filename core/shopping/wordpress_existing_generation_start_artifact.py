"""Content identity, not a Git packaging identity or review authorization.

The review digest is supplied from the independent canonical review record. Never
embed the resulting digest here: this verifier is itself part of the artifact.
"""
import hashlib
import json
import os
import stat
from pathlib import PurePosixPath

SUPPLIED_IMPLEMENTATION_BASELINE = '48bddf729f362e25f96eb110c53abff6bc4f46ae'
ARTIFACT_PATHS = ('core', 'ops', 'integrations', 'config', 'configs',
                  'requirements.txt', 'deploy/shopping/compose.yaml')
ARTIFACT_SCHEMA = 'SHOP-SERVICE-START-01G1G:reviewed-artifact:v1'


def artifact_identity(root, tracked_paths, safe_file):
    # Conservatively cover the tracked authority roots, including transitive
    # local imports, package initializers, contract data and dependency declarations.
    # The scope and verifier are themselves hashed. Git metadata is
    # outside this inventory, so packaging the same bytes in a new commit is safe.
    paths = sorted(tracked_paths)
    if not paths or len(paths) != len(set(paths)):
        raise ValueError('INVALID_ARTIFACT_INVENTORY')
    entries = []
    for name in paths:
        path = PurePosixPath(name)
        if path.is_absolute() or '..' in path.parts or str(path) != name:
            raise ValueError('INVALID_ARTIFACT_PATH')
        file = root / name
        safe_file(file)
        before = file.lstat()
        def identity(meta):
            return tuple(getattr(meta, field) for field in (
                'st_dev', 'st_ino', 'st_mode', 'st_uid', 'st_gid',
                'st_nlink', 'st_size', 'st_mtime_ns', 'st_ctime_ns'))
        with os.fdopen(os.open(file, os.O_RDONLY | os.O_NOFOLLOW), 'rb') as stream:
            opened = os.fstat(stream.fileno())
            if not stat.S_ISREG(opened.st_mode) or identity(opened) != identity(before):
                raise ValueError('ARTIFACT_FILE_DRIFT')
            raw = stream.read(65537)
            if len(raw) > 65536 or identity(os.fstat(stream.fileno())) != identity(before):
                raise ValueError('ARTIFACT_FILE_DRIFT')
        safe_file(file)
        if identity(file.lstat()) != identity(before):
            raise ValueError('ARTIFACT_FILE_DRIFT')
        entries.append([name, stat.S_IMODE(before.st_mode), hashlib.sha256(raw).hexdigest()])
    payload = json.dumps([ARTIFACT_SCHEMA, entries], ensure_ascii=True,
                         separators=(',', ':')).encode('ascii')
    return hashlib.sha256(payload).hexdigest()
