"""Dataset-isolated bridge to the pinned Meterless H-MEM reference.

Hash embeddings are a reference implementation, not learned semantic recall.
Retrieved memories are untrusted context, never instructions or fresh evidence.
"""
from __future__ import annotations
import hashlib
import fcntl
import re
import json
import os
from pathlib import Path
import subprocess


def dataset_fingerprint(files: dict[str, str]) -> str:
    digest = hashlib.sha256()
    for name, value in sorted(files.items()):
        if Path(name).name != name:
            raise ValueError('Use flat dataset file names')
        data_hash = hashlib.sha256(Path(value).read_bytes()).hexdigest()
        digest.update(json.dumps([name, data_hash], separators=(',', ':')).encode())
    return digest.hexdigest()


class EvidenceMemory:
    def __init__(self, dataset: str, state_dir: str | Path):
        if not re.fullmatch(r'[a-f0-9]{64}',dataset):
            raise ValueError('Dataset must be a SHA-256 fingerprint')
        self.dataset = dataset
        self.state_dir = str(Path(state_dir).resolve())

    def request(self, action: str, **payload):
        bridge = Path(__file__).resolve().parent / 'bridge' / 'hmem.ts'
        node = os.environ.get('RNA_NODE', 'node')
        request = dict(payload, action=action, dataset=self.dataset, state_dir=self.state_dir)
        locks=Path(self.state_dir)/'.locks'
        locks.mkdir(parents=True,exist_ok=True)
        with (locks/(self.dataset+'.lock')).open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            process = subprocess.run([node, '--experimental-transform-types', str(bridge)], input=json.dumps(request),
                                     text=True, capture_output=True, timeout=30, check=False)
        if process.returncode:
            raise RuntimeError('Memory bridge failed: ' + process.stderr[-2000:])
        return json.loads(process.stdout)

    def query(self, question):
        return self.request('query', query=question)

    def capture(self, content, source, tags=None):
        if not source or not content.strip():
            raise ValueError('Memory requires content and an evidence source')
        return self.request('add', content=content, source=source, tags=tags or [])
