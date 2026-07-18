import os
import yaml
from typing import Any, Dict

CONFIG_PATH: str = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config.yaml"))
_config_cache: Dict[str, Any] = {}

def load_config() -> Dict[str, Any]:
    if not _config_cache:
        with open(CONFIG_PATH) as f:
            data = yaml.safe_load(f)
            if data:
                _config_cache.update(data)
    return _config_cache

def reload_config() -> Dict[str, Any]:
    _config_cache.clear()
    return load_config()

def get_channel_id(name: str) -> int:
    cfg = load_config()
    return cfg.get("channels", {}).get(name, 0)

def get_guild_id() -> int:
    return load_config().get("guild_id", 0)

def get_config(key: str, default: Any = None) -> Any:
    cfg = load_config()
    keys = key.split(".")
    val = cfg
    for k in keys:
        if isinstance(val, dict):
            val = val.get(k)
        else:
            return default
    return val if val is not None else default

def save_config(cfg: Dict[str, Any]) -> None:
    _config_cache.clear()
    _config_cache.update(cfg)
    with open(CONFIG_PATH, "w") as f:
        yaml.dump(cfg, f, default_flow_style=False)
