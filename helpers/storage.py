import msgpack
import os
import threading
from collections import defaultdict
from typing import Any

DATA_DIR: str = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data"))
_locks: dict[str, threading.Lock] = defaultdict(threading.Lock)

def _path(name: str) -> str:
    return os.path.normpath(os.path.join(DATA_DIR, name))

def load(name: str) -> Any:
    path: str = _path(name)
    with _locks[name]:
        if os.path.exists(path):
            try:
                with open(path, "rb") as f:
                    data: Any = msgpack.unpackb(f.read(), raw=False)
                    return data if data else {}
            except (msgpack.UnpackException, OSError):
                pass
        return {}

def save(name: str, data: Any) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    path: str = _path(name)
    tmp: str = path + ".tmp"
    with _locks[name]:
        with open(tmp, "wb") as f:
            f.write(msgpack.packb(data, use_bin_type=True))
        os.replace(tmp, path)
