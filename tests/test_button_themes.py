import base64
from copy import deepcopy
import json
import struct
from unittest.mock import Mock, patch
import zlib

import pytest

from button_themes import ButtonThemes, MAX_REQUEST, validate_theme
from plugins.buttonstudio import buttonstudio


@pytest.fixture
def theme():
    return {
        "version": 1,
        "background": {
            "kind": "plasma",
            "color": "#6088B0",
            "gradient": {
                "angle": 135,
                "stops": [
                    {"color": "#6088B0", "position": 20},
                    {"color": "#ffcc00", "position": 100},
                ],
            },
            "speed": 24,
            "intensity": 65,
        },
        "text": {
            "color": "#ffffff",
            "gradient": None,
            "size": 20,
            "font": "rounded",
            "weight": 700,
            "angle": 360,
            "rotation": 10,
        },
        "icon": {"kind": "key", "image": "", "size": 36, "rotation": 12},
    }


def png(width=1, height=1):
    def chunk(kind, value):
        return (
            struct.pack(">I", len(value))
            + kind
            + value
            + struct.pack(">I", zlib.crc32(kind + value))
        )

    data = b"\x89PNG\r\n\x1a\n"
    data += chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
    data += chunk(b"IDAT", zlib.compress(b"\x00\x60\x88\xb0\xff"))
    data += chunk(b"IEND", b"")
    return "data:image/png;base64," + base64.b64encode(data).decode()


def test_designs_are_shared_survive_restart_and_keep_other_users(tmp_path, theme):
    first = ButtonThemes(tmp_path / "buttons.json")
    second = ButtonThemes(first.path)
    first.save("stitch", theme)
    other = deepcopy(theme)
    other["text"]["size"] = 30
    second.save("Jos", other)
    saved = first.all()
    assert saved["stitch"]["text"]["size"] == 20
    assert saved["Jos"]["text"]["size"] == 30
    assert saved["stitch"]["background"]["color"] == "#6088b0"


@pytest.mark.parametrize(
    "kind",
    [
        "shader-lights",
        "shader-snow",
        "shader-cubes",
        "shader-synthwave",
        "shader-wonderful",
        "shader-heartfelt",
        "shader-star-nest",
        "shader-clouds",
        "shader-universe",
        "shader-matrix",
    ],
)
def test_ambient_shaders_survive_restart_without_changing_other_settings(
    tmp_path, theme, kind
):
    theme["background"]["kind"] = kind
    store = ButtonThemes(tmp_path / "buttons.json")
    saved = store.save("stitch", theme)
    assert ButtonThemes(store.path).all()["stitch"] == saved
    assert saved["background"]["kind"] == kind
    assert saved["text"]["rotation"] == theme["text"]["rotation"]
    assert saved["icon"] == theme["icon"]


def test_shader_choices_do_not_allow_uploaded_source_or_urls(theme):
    theme["background"]["kind"] = "shader-https://example.test/demo"
    with pytest.raises(ValueError):
        validate_theme(theme)
    theme["background"]["kind"] = "shader-snow"
    theme["background"]["source"] = "void main() {}"
    with pytest.raises(ValueError):
        validate_theme(theme)


def test_uploaded_icons_stay_in_runtime_data_and_do_not_need_a_public_file(
    tmp_path, theme
):
    theme["icon"].update(kind="image", image=png())
    store = ButtonThemes(tmp_path / "buttons.json")
    store.save("stitch", theme)
    assert store.all()["stitch"]["icon"]["image"] == png()
    assert list(tmp_path.iterdir()) == [store.path]


@pytest.mark.parametrize(
    "path,value",
    [
        (("background", "color"), "red; position:fixed"),
        (("background", "speed"), 0),
        (("background", "intensity"), 101),
        (("background", "kind"), "url(https://example.test/image)"),
        (("text", "font"), "url(remote-font)"),
        (("text", "size"), 999),
        (("text", "angle"), -1),
        (("text", "rotation"), float("nan")),
        (("icon", "size"), True),
        (("icon", "image"), "data:image/svg+xml,<svg onload='alert(1)'/>"),
        (("icon", "image"), "https://example.test/icon.png"),
        (("icon", "image"), "data:image/png;base64,not-an-image"),
    ],
)
def test_unsafe_or_out_of_range_settings_are_rejected_before_writing(
    tmp_path, theme, path, value
):
    theme[path[0]][path[1]] = value
    store = ButtonThemes(tmp_path / "buttons.json")
    with pytest.raises(ValueError):
        store.save("stitch", theme)
    assert not store.path.exists()


def test_gradients_validate_stops_and_do_not_mutate_the_input(theme):
    theme["text"]["gradient"] = deepcopy(theme["background"]["gradient"])
    before = deepcopy(theme)
    assert validate_theme(theme)["text"]["gradient"]["stops"][0]["color"] == "#6088b0"
    assert theme == before
    theme["text"]["gradient"]["stops"][0]["position"] = 101
    with pytest.raises(ValueError):
        validate_theme(theme)


def test_older_saved_designs_load_without_rewriting_or_losing_their_settings(
    tmp_path, theme
):
    store = ButtonThemes(tmp_path / "buttons.json")
    store.path.write_text(json.dumps({"stitch": theme}))
    before = store.path.read_bytes()
    loaded = store.all()["stitch"]
    assert loaded["text"]["backdrop"] is None
    assert loaded["text"]["case"] == "original"
    assert {
        key: value
        for key, value in loaded["text"].items()
        if key not in {"backdrop", "case"}
    } == theme["text"]
    assert store.path.read_bytes() == before


@pytest.mark.parametrize(
    "case",
    [
        "original",
        "uppercase",
        "lowercase",
        "capitalize",
        "camel",
        "pascal",
        "snake",
        "kebab",
    ],
)
def test_cyber_and_name_case_survive_restart_without_changing_the_username(
    tmp_path, theme, case
):
    theme["background"]["kind"] = "shader-matrix"
    theme["text"].update(font="cyber", case=case)
    before = deepcopy(theme)
    store = ButtonThemes(tmp_path / "buttons.json")
    saved = store.save("BugBlue", theme)
    assert ButtonThemes(store.path).all() == {"BugBlue": saved}
    assert saved["text"]["font"] == "cyber"
    assert saved["text"]["case"] == case
    assert theme == before


@pytest.mark.parametrize("case", ["title", "UPPERCASE", "", None, 42, {}, []])
def test_unknown_name_cases_are_rejected(theme, case):
    theme["text"]["case"] = case
    with pytest.raises(ValueError):
        validate_theme(theme)


def test_backdrops_save_and_reload_with_gradient_and_rotating_text(tmp_path, theme):
    store = ButtonThemes(tmp_path / "buttons.json")
    theme["text"]["backdrop"] = {
        "color": "#FFFFFF",
        "opacity": 65,
        "padding": 6,
        "radius": 12,
    }
    theme["text"]["gradient"] = deepcopy(theme["background"]["gradient"])
    store.save("stitch", theme)
    saved = ButtonThemes(store.path).all()["stitch"]["text"]
    assert saved["backdrop"] == {
        "color": "#ffffff",
        "opacity": 65,
        "padding": 6,
        "radius": 12,
    }
    assert saved["rotation"] == theme["text"]["rotation"]
    assert saved["gradient"]["angle"] == theme["text"]["gradient"]["angle"]
    theme["text"]["backdrop"] = None
    store.save("stitch", theme)
    assert store.all()["stitch"]["text"]["backdrop"] is None


@pytest.mark.parametrize(
    "property_name,value",
    [
        ("color", "url(https://example.test/image)"),
        ("opacity", 101),
        ("padding", -1),
        ("radius", 21),
    ],
)
def test_invalid_backdrop_settings_are_rejected(theme, property_name, value):
    backdrop = {"color": "#ffffff", "opacity": 65, "padding": 6, "radius": 12}
    backdrop[property_name] = value
    theme["text"]["backdrop"] = backdrop
    with pytest.raises(ValueError):
        validate_theme(theme)


@pytest.mark.parametrize("stop_count", [0, 1, 7])
def test_gradient_stop_counts_are_bounded(theme, stop_count):
    theme["background"]["gradient"]["stops"] = [
        {"color": "#ffffff", "position": 0}
    ] * stop_count
    with pytest.raises(ValueError):
        validate_theme(theme)


def test_icon_bounds_and_unknown_settings_are_rejected(theme):
    theme["icon"].update(kind="image", image=png(10000, 1))
    with pytest.raises(ValueError):
        validate_theme(theme)
    theme["icon"].update(kind="none", image="")
    theme["text"]["css"] = "position:fixed"
    with pytest.raises(ValueError):
        validate_theme(theme)


def test_failed_atomic_write_preserves_previous_designs_and_cleans_up(tmp_path, theme):
    store = ButtonThemes(tmp_path / "buttons.json")
    store.save("stitch", theme)
    before = store.path.read_bytes()
    with patch("button_themes.os.replace", side_effect=OSError("read-only")):
        with pytest.raises(OSError):
            store.save("Jos", theme)
    assert store.path.read_bytes() == before
    assert list(tmp_path.iterdir()) == [store.path]


def test_corrupt_storage_is_reported_without_overwriting_it(tmp_path, theme):
    store = ButtonThemes(tmp_path / "buttons.json")
    store.path.write_text("broken json")
    with pytest.raises(ValueError, match="could not be read"):
        store.save("stitch", theme)
    assert store.path.read_text() == "broken json"


def test_settings_route_publishes_only_after_save_and_never_touches_a_sale(
    tmp_path, theme
):
    master = Mock()
    master.accounts.accounts = {"stitch": {"amount": 7}}
    pending = {"plug": Mock(), "function": "answer"}
    master.nextcall = pending
    plugin = buttonstudio("sid", master, ButtonThemes(tmp_path / "buttons.json"))
    plugin.configure(
        json.dumps({"request": "save-1", "user": "stitch", "theme": theme}).encode()
    )
    reply = json.loads(master.send_message.call_args.args[2])
    assert reply["ok"] is True
    assert reply["theme"]["text"]["size"] == 20
    master.client.publish.assert_called_once()
    topic, payload = master.client.publish.call_args.args
    assert topic == "hack42bar/output/settings/buttons/stitch"
    assert json.loads(payload)["theme"] == reply["theme"]
    assert master.nextcall is pending
    master.input.assert_not_called()
    master.callhook.assert_not_called()


def test_read_does_not_write_and_missing_user_is_rejected(tmp_path):
    master = Mock()
    master.accounts.accounts = {"stitch": {}}
    store = ButtonThemes(tmp_path / "buttons.json")
    plugin = buttonstudio("sid", master, store)
    plugin.configure(b'{"request":"read-1","user":"stitch"}')
    assert json.loads(master.send_message.call_args.args[2])["theme"] is None
    assert not store.path.exists()
    plugin.configure(b'{"request":"read-2","user":"unknown"}')
    assert json.loads(master.send_message.call_args.args[2])["ok"] is False
    plugin.configure(b"x" * (MAX_REQUEST + 1))
    assert json.loads(master.send_message.call_args.args[2])["ok"] is False


def test_settings_save_error_does_not_publish_a_design_that_was_not_saved(
    tmp_path, theme
):
    master = Mock()
    master.accounts.accounts = {"stitch": {}}
    store = ButtonThemes(tmp_path / "buttons.json")
    plugin = buttonstudio("sid", master, store)
    with patch.object(store, "save", side_effect=OSError("read-only")):
        plugin.configure(
            json.dumps({"request": "save-1", "user": "stitch", "theme": theme}).encode()
        )
    assert json.loads(master.send_message.call_args.args[2])["ok"] is False
    master.client.publish.assert_not_called()
