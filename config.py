import copy
import os

import yaml


CONFIG_PATH = "config.yaml"

DEFAULT_CONFIG = {
    "mqtt": {
        "host": "localhost",
        "port": 1883,
        "keepalive": 60,
    },
    "door": {
        "mqtt": {
            "host": "mqtt.space.hack42.nl",
            "port": 1883,
            "keepalive": 60,
            "topic": "hack42/brandhok/deuropen",
        },
    },
    "stickers": {
        "printer": {
            "model": "QL-710W",
            "host": "localhost",
            "port": 9100,
        },
    },
    "pos": {
        "serial": {
            "port": "/dev/ttyUSB0",
            "baudrate": 19200,
        },
    },
    "logging": {
        "level": "INFO",
    },
}


def _merge_config(base, override):
    merged = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge_config(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_config(path=None):
    path = path or os.environ.get("KASSA_CONFIG", CONFIG_PATH)
    if not os.path.exists(path):
        return copy.deepcopy(DEFAULT_CONFIG)

    with open(path, encoding="utf-8") as config_file:
        loaded = yaml.safe_load(config_file) or {}

    if not isinstance(loaded, dict):
        return copy.deepcopy(DEFAULT_CONFIG)
    return _merge_config(DEFAULT_CONFIG, loaded)


def config_get(*keys, default=None):
    value = load_config()
    for key in keys:
        if not isinstance(value, dict) or key not in value:
            return default
        value = value[key]
    return value
