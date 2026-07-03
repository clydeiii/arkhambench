from __future__ import annotations

import base64
import hashlib
import json
import os
import zlib
from pathlib import Path
from typing import Any


HIDDEN_PREAMBLE = "DO NOT READ - hidden ArkhamBench state\n"
_KEY = b"ArkhamBench phase A hidden state hygiene key"


def _xor(data: bytes) -> bytes:
    return bytes(byte ^ _KEY[index % len(_KEY)] for index, byte in enumerate(data))


def encode_hidden(data: dict[str, Any]) -> str:
    raw = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    compressed = zlib.compress(raw)
    encoded = base64.b64encode(_xor(compressed)).decode("ascii")
    return HIDDEN_PREAMBLE + encoded + "\n"


def decode_hidden(text: str) -> dict[str, Any]:
    if not text.startswith(HIDDEN_PREAMBLE):
        raise ValueError("hidden blob preamble missing")
    payload = "".join(text[len(HIDDEN_PREAMBLE) :].split())
    compressed = _xor(base64.b64decode(payload.encode("ascii")))
    raw = zlib.decompress(compressed)
    return json.loads(raw.decode("utf-8"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.tmp")
    with temp.open("w", encoding="utf-8") as handle:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp, path)


def atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    text = json.dumps(data, indent=2, sort_keys=True) + "\n"
    atomic_write_text(path, text)
