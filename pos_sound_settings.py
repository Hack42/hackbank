"""Shared POS sound choices, backed by an atomic file in the app's data directory."""

import json
import logging
import os
from pathlib import Path
import tempfile
import threading

logger = logging.getLogger(__name__)

DEFAULTS = {
    "command": "KDE_Beep_ClassicBeep.wav",
    "deposit": "itsgone.wav",
    "insufficient_funds": "sinterklaas.wav",
    "sale": "katsjing.wav",
    "error": "KDE_Beep_Beep.wav",
}
LABELS = {
    "command": "Command",
    "deposit": "Deposit",
    "insufficient_funds": "Insufficient funds",
    "sale": "Sale",
    "error": "Error",
}
SOUND_ROOT = Path(__file__).resolve().parent / "www" / "sounds"


class POSSoundSettings:
    write_lock = threading.Lock()

    def __init__(self, path="data/revbank.sounds.json", root=SOUND_ROOT):
        self.path = Path(path)
        self.root = Path(root)

    def _choices(self, feature):
        return sorted(
            (
                path.name
                for path in (self.root / "POS" / feature).iterdir()
                if path.is_file()
                and not path.is_symlink()
                and path.suffix.lower() in (".wav", ".mp3", ".ogg")
            ),
            key=str.casefold,
        )

    def _read(self):
        try:
            saved = json.loads(self.path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return {}
        except (UnicodeError, json.JSONDecodeError) as error:
            raise ValueError("Saved sound settings could not be read.") from error
        if not isinstance(saved, dict):
            raise ValueError("Saved sound settings could not be read.")
        return saved

    def state(self):
        saved = self._read()
        features = []
        for feature, default in DEFAULTS.items():
            choices = self._choices(feature)
            if default not in choices:
                raise ValueError("A default POS sound is missing.")
            selected = saved.get(feature)
            features.append(
                {
                    "id": feature,
                    "label": LABELS[feature],
                    "default": default,
                    "selected": selected if selected in choices else default,
                    "choices": choices,
                }
            )
        return {"features": features}

    def sample(self, feature):
        default = DEFAULTS[feature]
        try:
            selected = self._read().get(feature, default)
            if not isinstance(selected, str) or selected not in self._choices(feature):
                selected = default
        except (OSError, ValueError):
            logger.warning(
                "pos_sound_settings_unavailable; using defaults", exc_info=True
            )
            selected = default
        return "POS/" + feature + "/" + selected

    def _write(self, selected):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(
            prefix=self.path.name + ".", dir=self.path.parent, text=True
        )
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as output:
                json.dump(selected, output, sort_keys=True)
                output.write("\n")
            os.replace(temporary, self.path)
        except Exception:
            Path(temporary).unlink(missing_ok=True)
            raise

    def set(self, feature, sound):
        if (
            not isinstance(feature, str)
            or feature not in DEFAULTS
            or not isinstance(sound, str)
        ):
            raise ValueError("Unknown POS sound feature.")
        with self.write_lock:
            if sound not in self._choices(feature):
                raise ValueError("Choose a sound from this feature's folder.")
            selected = {
                item["id"]: item["selected"] for item in self.state()["features"]
            }
            selected[feature] = sound
            self._write(selected)
            return self.state()

    def reset(self, feature=None):
        if feature is not None:
            if not isinstance(feature, str) or feature not in DEFAULTS:
                raise ValueError("Unknown POS sound feature.")
            return self.set(feature, DEFAULTS[feature])
        with self.write_lock:
            self._write(dict(DEFAULTS))
            return self.state()
