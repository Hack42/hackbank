import json
from unittest.mock import patch
import wave

import pytest

from plugins.sounds import SOUND_SAMPLES
from pos_sound_settings import DEFAULTS, POSSoundSettings, SOUND_ROOT


def test_bundled_defaults_and_soundboard_files_are_valid_and_in_the_right_folders():
    settings = POSSoundSettings()
    for feature, default in DEFAULTS.items():
        assert settings.sample(feature) == f"POS/{feature}/{default}"
        assert default in settings._choices(feature)
    for relative in {
        *SOUND_SAMPLES.values(),
        *(f"POS/{key}/{name}" for key, name in DEFAULTS.items()),
    }:
        path = SOUND_ROOT / relative
        assert path.is_file()
        if path.suffix == ".wav":
            with wave.open(str(path), "rb") as audio:
                assert audio.getnframes() > 0
        else:
            assert path.read_bytes().startswith(b"ID3") or path.read_bytes()[0] == 255


def test_selections_survive_restart_and_are_shared_between_instances(tmp_path):
    first = POSSoundSettings(tmp_path / "sounds.json")
    second = POSSoundSettings(first.path)
    first.set("deposit", "money.wav")
    assert second.sample("deposit") == "POS/deposit/money.wav"
    second.set("sale", "cash_tycoon.wav")
    assert first.sample("sale") == "POS/sale/cash_tycoon.wav"
    assert first.sample("deposit") == "POS/deposit/money.wav"
    assert json.loads(first.path.read_text())["sale"] == "cash_tycoon.wav"


def test_reset_one_feature_preserves_other_choices_and_reset_all_restores_defaults(
    tmp_path,
):
    settings = POSSoundSettings(tmp_path / "sounds.json")
    settings.set("deposit", "money.wav")
    settings.set("sale", "cash_tycoon.wav")
    settings.reset("deposit")
    assert settings.sample("deposit") == "POS/deposit/itsgone.wav"
    assert settings.sample("sale") == "POS/sale/cash_tycoon.wav"
    settings.reset()
    assert json.loads(settings.path.read_text()) == DEFAULTS


@pytest.mark.parametrize(
    "feature,sound",
    [
        ("sale", "../deposit/money.wav"),
        ("sale", "money.wav"),
        ("command", "/etc/passwd"),
        ("unknown", "katsjing.wav"),
        ([], "katsjing.wav"),
        ("sale", None),
    ],
)
def test_choices_are_limited_to_files_in_the_matching_feature_folder(
    tmp_path, feature, sound
):
    settings = POSSoundSettings(tmp_path / "sounds.json")
    with pytest.raises(ValueError):
        settings.set(feature, sound)
    assert not settings.path.exists()


def test_failed_write_keeps_previous_saved_settings_and_cleans_temporary_file(tmp_path):
    settings = POSSoundSettings(tmp_path / "sounds.json")
    settings.set("sale", "cash_tycoon.wav")
    before = settings.path.read_bytes()
    with patch("pos_sound_settings.os.replace", side_effect=OSError("read-only")):
        with pytest.raises(OSError):
            settings.set("sale", "katsjing.wav")
    assert settings.path.read_bytes() == before
    assert list(tmp_path.iterdir()) == [settings.path]


def test_corrupt_settings_keep_playback_defaults_and_can_be_reset(tmp_path):
    settings = POSSoundSettings(tmp_path / "sounds.json")
    settings.path.write_text("not json")
    assert settings.sample("sale") == "POS/sale/katsjing.wav"
    with pytest.raises(ValueError):
        settings.state()
    settings.reset()
    assert json.loads(settings.path.read_text()) == DEFAULTS


def test_missing_selected_file_falls_back_to_default_and_hidden_files_are_ignored(
    tmp_path,
):
    root = tmp_path / "sounds"
    for feature, default in DEFAULTS.items():
        directory = root / "POS" / feature
        directory.mkdir(parents=True)
        (directory / default).write_bytes(b"wav")
        (directory / ".DS_Store").write_bytes(b"metadata")
    settings = POSSoundSettings(tmp_path / "choices.json", root)
    extra = root / "POS" / "sale" / "extra.wav"
    extra.write_bytes(b"wav")
    settings.set("sale", extra.name)
    extra.unlink()
    assert settings.sample("sale") == "POS/sale/katsjing.wav"
    state = settings.state()
    assert all(item["choices"] == [DEFAULTS[item["id"]]] for item in state["features"])
