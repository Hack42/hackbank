"""Presentation-only button designs stored with the bar's private runtime data."""

import base64
import binascii
import json
import os
from pathlib import Path
import re
import struct
import tempfile
import threading

MAX_REQUEST = 160 * 1024
MAX_ICON_BYTES = 96 * 1024
FONTS = {"system", "rounded", "comic", "mono", "serif", "condensed"}
ICONS = {"none", "image", "key", "star", "bolt", "heart", "smile"}


def fields(value, names):
    if not isinstance(value, dict) or set(value) != set(names.split()):
        raise ValueError("This button design has missing or unknown settings.")
    return value


def number(value, low, high):
    if type(value) not in (int, float) or not low <= value <= high:
        raise ValueError("A button setting is outside its allowed range.")
    return value


def choice(value, choices):
    if not isinstance(value, str) or value not in choices:
        raise ValueError("Unknown button style.")
    return value


def color(value):
    if not isinstance(value, str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
        raise ValueError("Use a six-digit hex colour, such as #6088B0.")
    return value.lower()


def gradient(value):
    fields(value, "angle stops")
    stops = value["stops"]
    if not isinstance(stops, list) or not 2 <= len(stops) <= 6:
        raise ValueError("A gradient needs between two and six colour stops.")
    result = []
    for stop in stops:
        fields(stop, "color position")
        result.append(
            {
                "color": color(stop["color"]),
                "position": number(stop["position"], 0, 100),
            }
        )
    return {"angle": number(value["angle"], 0, 360), "stops": result}


def icon_image(value):
    if not isinstance(value, str):
        raise ValueError("Choose an image for your icon.")
    if not value:
        return ""
    prefix = "data:image/png;base64,"
    if not value.startswith(prefix) or len(value) > MAX_ICON_BYTES * 4 // 3 + len(
        prefix
    ):
        raise ValueError("Icon images must be small PNG images.")
    try:
        raw = base64.b64decode(value[len(prefix) :], validate=True)
    except (ValueError, binascii.Error) as error:
        raise ValueError("This icon image could not be read.") from error
    if (
        len(raw) < 45
        or not raw.startswith(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")
        or not raw.endswith(b"\x00\x00\x00\x00IEND\xaeB`\x82")
    ):
        raise ValueError("This icon image could not be read.")
    width, height = struct.unpack(">II", raw[16:24])
    if not 1 <= width <= 144 or not 1 <= height <= 144:
        raise ValueError("Icon images must be resized to at most 144 pixels.")
    return value


def label_backdrop(value):
    if value is None:
        return None
    fields(value, "color opacity padding radius")
    return {
        "color": color(value["color"]),
        "opacity": number(value["opacity"], 0, 100),
        "padding": number(value["padding"], 0, 12),
        "radius": number(value["radius"], 0, 20),
    }


def validate_theme(value):
    fields(value, "version background text icon")
    if (
        not isinstance(value["version"], int)
        or isinstance(value["version"], bool)
        or value["version"] != 1
    ):
        raise ValueError("Unknown button design version.")
    background = fields(value["background"], "kind color gradient speed intensity")
    # Existing version-1 designs predate configurable label backdrops.
    text = value["text"]
    if isinstance(text, dict):
        text = {"backdrop": None, **text}
    text = fields(text, "color gradient size font weight angle rotation backdrop")
    icon = fields(value["icon"], "kind image size rotation")
    image = icon_image(icon["image"])
    kind = choice(icon["kind"], ICONS)
    if kind == "image" and not image:
        raise ValueError("Choose an image for your icon.")
    return {
        "version": 1,
        "background": {
            "kind": choice(
                background["kind"],
                {
                    "solid",
                    "gradient",
                    "glitter",
                    "plasma",
                    "shader-lights",
                    "shader-snow",
                    "shader-cubes",
                    "shader-synthwave",
                },
            ),
            "color": color(background["color"]),
            "gradient": gradient(background["gradient"]),
            "speed": number(background["speed"], 2, 60),
            "intensity": number(background["intensity"], 0, 100),
        },
        "text": {
            "color": color(text["color"]),
            "gradient": (
                gradient(text["gradient"]) if text["gradient"] is not None else None
            ),
            "size": number(text["size"], 10, 48),
            "font": choice(text["font"], FONTS),
            "weight": number(text["weight"], 400, 900),
            "angle": number(text["angle"], 0, 360),
            "rotation": number(text["rotation"], 0, 60),
            "backdrop": label_backdrop(text["backdrop"]),
        },
        "icon": {
            "kind": kind,
            "image": image if kind == "image" else "",
            "size": number(icon["size"], 20, 64),
            "rotation": number(icon["rotation"], 0, 60),
        },
    }


class ButtonThemes:
    write_lock = threading.Lock()

    def __init__(self, path="data/revbank.buttons.json"):
        self.path = Path(path)

    def all(self):
        try:
            saved = json.loads(self.path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return {}
        except (UnicodeError, json.JSONDecodeError) as error:
            raise ValueError("Saved button designs could not be read.") from error
        if not isinstance(saved, dict):
            raise ValueError("Saved button designs could not be read.")
        return {name: validate_theme(theme) for name, theme in saved.items()}

    def save(self, user, theme):
        theme = validate_theme(theme)
        with self.write_lock:
            saved = self.all()
            saved[user] = theme
            self.path.parent.mkdir(parents=True, exist_ok=True)
            descriptor, temporary = tempfile.mkstemp(
                prefix=self.path.name + ".", dir=self.path.parent, text=True
            )
            try:
                with os.fdopen(descriptor, "w", encoding="utf-8") as output:
                    json.dump(saved, output, ensure_ascii=True)
                    output.write("\n")
                os.replace(temporary, self.path)
            except Exception:
                Path(temporary).unlink(missing_ok=True)
                raise
        return theme
