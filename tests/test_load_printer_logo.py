from pathlib import Path
import runpy
import struct
from unittest.mock import Mock, patch

from PIL import Image
import pytest

import load_printer_logo as loader
from plugins.POS import CENTER, CUT, FEED, LOGO, PRINTER


def test_column_encoding_transparency_and_padding(tmp_path):
    path = tmp_path / "logo.png"
    image = Image.new("RGBA", (9, 9), (0, 0, 0, 0))
    image.putpixel((0, 0), (0, 0, 0, 255))
    image.putpixel((8, 8), (0, 0, 0, 255))
    image.save(path)

    payload = loader.encode_logo(path)

    expected = bytearray(32)
    expected[0] = 0x80
    expected[17] = 0x80
    assert payload == b"\x1cq\x01" + struct.pack("<HH", 2, 2) + expected


def test_logo_scales_proportionally(tmp_path):
    path = tmp_path / "logo.png"
    Image.new("RGB", (32, 16), "black").save(path)
    assert loader.encode_logo(path, 16) == (
        b"\x1cq\x01" + struct.pack("<HH", 2, 1) + b"\xff" * 16
    )


def test_only_near_white_pixels_remain_white(tmp_path):
    path = tmp_path / "colors.png"
    image = Image.new("RGB", (8, 1))
    image.putdata(
        [
            (255, 255, 255),
            (245, 245, 245),
            (244, 244, 244),
            (180, 180, 180),
            (255, 255, 0),
            (255, 255, 200),
            (244, 255, 255),
            (0, 0, 0),
        ]
    )
    image.save(path)

    assert loader.encode_logo(path)[7:] == b"\x00\x00" + b"\x80" * 6


@pytest.mark.parametrize("width", [0, 513])
def test_invalid_width_does_not_load_or_upload(width):
    with pytest.raises(ValueError):
        loader.encode_logo("missing.png", width)


@pytest.mark.parametrize("test_print", [False, True])
def test_upload_writes_complete_command_and_optional_existing_logo(test_print):
    printer = Mock()
    printer.write.side_effect = len
    payload = b"\x1cq\x01" + bytes(80)
    with patch.object(loader.serial, "Serial") as serial_mock, patch.object(
        loader.time, "sleep"
    ):
        serial_mock.return_value.__enter__.return_value = printer
        loader.upload_logo("/dev/test", 19200, payload, test_print)

    serial_mock.assert_called_once_with(
        port="/dev/test", baudrate=19200, timeout=5, write_timeout=10, exclusive=True
    )
    written = b"".join(call.args[0] for call in printer.write.call_args_list)
    proof = PRINTER + CENTER + LOGO + FEED + CUT if test_print else b""
    assert written == PRINTER + payload + proof
    assert printer.flush.call_count == (2 if test_print else 1)


@pytest.mark.parametrize("results", [[0], [len(PRINTER) + 1, 0]])
def test_upload_rejects_short_writes(results):
    with patch.object(loader.serial, "Serial") as serial_mock, patch.object(
        loader.time, "sleep"
    ):
        serial_mock.return_value.__enter__.return_value.write.side_effect = results
        with pytest.raises(OSError, match="Incomplete serial write"):
            loader.upload_logo("/dev/test", 19200, b"x", test_print=True)


def test_cli_default_is_offline_and_exports_payload(tmp_path, capsys):
    output = tmp_path / "logo.bin"
    with patch.object(loader, "upload_logo") as upload:
        loader.main(["--output", str(output)])
    upload.assert_not_called()
    assert output.read_bytes().startswith(b"\x1cq\x01")
    assert "Use --write" in capsys.readouterr().out


def test_cli_uses_serial_config(tmp_path, capsys):
    config = tmp_path / "config.yaml"
    config.write_text(
        "pos:\n  serial:\n    port: /dev/configured\n    baudrate: 9600\n"
    )
    with patch.object(loader, "upload_logo") as upload:
        loader.main(["--config", str(config), "--write", "--test-print"])
    assert upload.call_args.args[:2] == ("/dev/configured", 9600)
    assert upload.call_args.args[3] is True
    assert "verify with a test print" in capsys.readouterr().out


def test_cli_serial_overrides():
    with patch.object(loader, "upload_logo") as upload:
        loader.main(["--write", "--port", "/dev/override", "--baudrate", "4800"])
    assert upload.call_args.args[:2] == ("/dev/override", 4800)


def test_cli_print_requires_write():
    with pytest.raises(SystemExit) as error:
        loader.main(["--test-print"])
    assert error.value.code == 2


def test_cli_serial_error_has_nonzero_exit(capsys):
    with patch.object(loader, "upload_logo", side_effect=OSError("port busy")):
        with pytest.raises(SystemExit) as error:
            loader.main(["--write"])
    assert error.value.code == 1
    assert "port busy" in capsys.readouterr().err


def test_cli_entrypoint_is_offline(capsys):
    with patch("sys.argv", ["load_printer_logo.py"]):
        runpy.run_path(str(Path(loader.__file__)), run_name="__main__")
    assert "Use --write" in capsys.readouterr().out
