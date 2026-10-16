"""Upload NV logo 1 for the existing Epson FS p receipt header."""

import argparse
from pathlib import Path
import struct
import time

from PIL import Image, ImageChops, ImageOps
import serial

from config import load_config
from plugins.POS import CENTER, CUT, FEED, LOGO, PRINTER


def encode_logo(path, width=192):
    """Encode FS q column data; LOGO prints this at twice the stored size."""
    if not 8 <= width <= 512:
        raise ValueError("Stored width must be between 8 and 512 dots")
    with Image.open(path) as source:
        image = source.convert("RGBA")
    image.thumbnail((width, 512), Image.Resampling.LANCZOS)
    white = Image.new("RGBA", image.size, "white")
    red, green, blue = Image.alpha_composite(white, image).convert("RGB").split()
    # Keep only near-white pixels white, including bright saturated colors as ink.
    darkest = ImageChops.darker(ImageChops.darker(red, green), blue)
    ink = ImageOps.invert(darkest.point(lambda value: 255 if value >= 245 else 0))
    x_bytes, y_bytes = (image.width + 7) // 8, (image.height + 7) // 8
    padded = Image.new("1", (x_bytes * 8, y_bytes * 8), 0)
    padded.paste(ink.convert("1"), (0, 0))
    # FS q packs each column from top to bottom, most significant bit first.
    columns = padded.transpose(Image.Transpose.TRANSPOSE).tobytes()
    return b"\x1cq\x01" + struct.pack("<HH", x_bytes, y_bytes) + columns


def upload_logo(port, baudrate, payload, test_print=False):
    """Write once, then allow the printer to finish its NV write/reset."""
    with serial.Serial(
        port=port, baudrate=baudrate, timeout=5, write_timeout=10, exclusive=True
    ) as printer:
        data = PRINTER + payload
        for offset in range(0, len(data), 32):
            chunk = data[offset : offset + 32]
            if printer.write(chunk) != len(chunk):
                raise OSError("Incomplete serial write; logo upload interrupted")
            time.sleep(0.05)
        printer.flush()
        time.sleep(5)
        if test_print:
            proof = PRINTER + CENTER + LOGO + FEED + CUT
            if printer.write(proof) != len(proof):
                raise OSError("Incomplete serial write during test print")
            printer.flush()


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Store Epson NV logo 1. Replaces ALL existing NV logos. "
        "Stop the kassa backend first and keep the printer powered on."
    )
    parser.add_argument(
        "image",
        nargs="?",
        type=Path,
        default=Path(__file__).resolve().parent / "images/hack42.png",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=192,
        help="stored width in dots; receipts print at 2x (default: 192)",
    )
    parser.add_argument("--config", type=Path, help="config.yaml override")
    parser.add_argument("--port", help="override pos.serial.port")
    parser.add_argument("--baudrate", type=int, help="override pos.serial.baudrate")
    parser.add_argument("--output", type=Path, help="export FS q bytes to a file")
    parser.add_argument("--write", action="store_true", help="replace printer NV logos")
    parser.add_argument(
        "--test-print", action="store_true", help="print logo after upload"
    )
    args = parser.parse_args(argv)
    if args.test_print and not args.write:
        parser.error("--test-print requires --write")
    try:
        payload = encode_logo(args.image, args.width)
        if args.output:
            args.output.write_bytes(payload)
        if args.write:
            settings = load_config(args.config)["pos"]["serial"]
            upload_logo(
                args.port or settings["port"],
                args.baudrate or int(settings["baudrate"]),
                payload,
                args.test_print,
            )
            print("NV logo 1 sent to printer; verify with a test print.")
        else:
            print(
                f"Prepared {len(payload)} bytes. Use --write to replace printer NV logos."
            )
    except (OSError, ValueError, serial.SerialException) as exc:
        parser.exit(1, f"Logo upload failed: {exc}\n")


if __name__ == "__main__":
    main()
