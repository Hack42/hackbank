import os

from config import config_get, load_config


def test_load_config_uses_defaults_when_missing(tmp_path):
    config = load_config(tmp_path / "missing.yaml")

    assert config["mqtt"]["host"] == "localhost"
    assert config["stickers"]["printer"]["port"] == 9100
    assert config["logging"]["level"] == "INFO"


def test_load_config_merges_yaml_with_defaults(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "mqtt:\n"
        "  host: mqtt.example.test\n"
        "stickers:\n"
        "  printer:\n"
        "    host: printer.example.test\n",
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config["mqtt"]["host"] == "mqtt.example.test"
    assert config["mqtt"]["port"] == 1883
    assert config["stickers"]["printer"]["host"] == "printer.example.test"
    assert config["stickers"]["printer"]["port"] == 9100
    assert config["logging"]["level"] == "INFO"


def test_load_config_uses_defaults_for_non_mapping_yaml(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text("- not\n- a\n- mapping\n", encoding="utf-8")

    config = load_config(config_path)

    assert config["mqtt"]["host"] == "localhost"
    assert config["stickers"]["printer"]["port"] == 9100


def test_config_get_uses_env_path(tmp_path, monkeypatch):
    config_path = tmp_path / "custom.yaml"
    config_path.write_text("mqtt:\n  port: 1884\n", encoding="utf-8")
    monkeypatch.setenv("KASSA_CONFIG", str(config_path))

    assert config_get("mqtt", "port") == 1884
    assert config_get("missing", default="fallback") == "fallback"


def test_example_config_loads():
    config = load_config("config.yaml.example")

    assert config["stickers"]["printer"]["host"] == "BRW008092D4A414.space.hack42.nl"
    assert os.path.basename("config.yaml.example") == "config.yaml.example"
