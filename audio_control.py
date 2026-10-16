"""Expose only the two HackBank output volumes over a local Unix socket."""

import argparse
from http.server import BaseHTTPRequestHandler
import json
import os
from pathlib import Path
import socketserver
import stat
import subprocess
import threading


OUTPUTS = {"pos": "hackbank_pos", "space": "snapcast"}
PREVIEW_SOUND = Path(__file__).resolve().parent / "www/sounds/KDE_Beep_ClassicBeep.wav"


def validate_volume(channel, volume, preview=False):
    if channel not in OUTPUTS:
        raise ValueError("Unknown audio output")
    if type(volume) is not int or not 0 <= volume <= 100:
        raise ValueError("Volume must be an integer from 0 to 100")
    if type(preview) is not bool:
        raise ValueError("Preview must be a boolean")


class PulseAudio:
    def __init__(self, run=None, play=None):
        self.run = run or self._run
        self.play = play or self._play

    @staticmethod
    def _run(*args):
        return subprocess.run(
            ["/usr/bin/pactl", *args], check=True, capture_output=True,
            text=True, timeout=4,
        ).stdout

    @staticmethod
    def _play(sink):
        subprocess.run(
            ["/usr/bin/paplay", f"--device={sink}", "--volume=65536",
             "--client-name=HackBank volume preview", "--stream-name=HackBank volume preview",
             str(PREVIEW_SOUND)],
            check=True, capture_output=True, timeout=4,
        )

    def read(self):
        sinks = {sink["name"]: sink for sink in json.loads(self.run("-f", "json", "list", "sinks"))}
        channels = {}
        for channel, name in OUTPUTS.items():
            sink = sinks.get(name)
            values = [entry["value"] for entry in sink.get("volume", {}).values()] if sink else []
            channels[channel] = {
                "available": bool(values),
                "volume": round(sum(values) / len(values) * 100 / 65536) if values else None,
                "muted": bool(sink and sink.get("mute")),
            }
        return {"channels": channels}

    def set(self, channel, volume, preview=False):
        validate_volume(channel, volume, preview)
        if not self.read()["channels"][channel]["available"]:
            raise RuntimeError("Audio output is unavailable")
        self.run("set-sink-volume", OUTPUTS[channel], f"{volume}%")
        self.run("set-sink-mute", OUTPUTS[channel], "1" if volume == 0 else "0")
        state = self.read()
        if preview:
            state["preview_played"] = False
            if volume > 0:
                try:
                    self.play(OUTPUTS[channel])
                    state["preview_played"] = True
                except (OSError, subprocess.SubprocessError):
                    state["preview_error"] = True
        return state


class DemoAudio:
    """Development-only state; never connects to an audio device."""
    def __init__(self):
        self.volumes = {"pos": 35, "space": 70}
        self.previews = []

    def read(self):
        return {"channels": {
            channel: {"available": True, "volume": volume, "muted": volume == 0}
            for channel, volume in self.volumes.items()
        }}

    def set(self, channel, volume, preview=False):
        validate_volume(channel, volume, preview)
        self.volumes[channel] = volume
        state = self.read()
        if preview:
            state["preview_played"] = volume > 0
            if volume > 0:
                self.previews.append(channel)
        return state


class AudioRequest(BaseHTTPRequestHandler):
    def setup(self):
        super().setup()
        self.connection.settimeout(5)

    def address_string(self):
        return "local"

    def _reply(self, status, body):
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _dispatch(self, write=False):
        if self.path != "/volume":
            self._reply(404, {"error": "Unknown endpoint"})
            return
        try:
            with self.server.audio_lock:
                if write:
                    if self.headers.get_content_type() != "application/json":
                        self._reply(415, {"error": "JSON required"})
                        return
                    length = int(self.headers.get("Content-Length", "0"))
                    if not 0 < length <= 256:
                        raise ValueError("Invalid request length")
                    request = json.loads(self.rfile.read(length))
                    if (not isinstance(request, dict) or not {"channel", "volume"} <= set(request)
                            or set(request) - {"channel", "volume", "preview"}):
                        raise ValueError("Invalid volume request")
                    state = self.server.audio.set(request["channel"], request["volume"], request.get("preview", False))
                else:
                    state = self.server.audio.read()
            self._reply(200, state)
        except (ValueError, TypeError, KeyError):
            self._reply(400, {"error": "Invalid volume request"})
        except (OSError, RuntimeError, subprocess.SubprocessError):
            self._reply(503, {"error": "Audio system is unavailable"})

    def do_GET(self):  # pylint: disable=invalid-name
        self._dispatch()

    def do_POST(self):  # pylint: disable=invalid-name
        self._dispatch(write=True)


class AudioServer(socketserver.ThreadingUnixStreamServer):
    daemon_threads = True

    def __init__(self, path, audio):
        self.audio = audio
        self.audio_lock = threading.Lock()
        super().__init__(path, AudioRequest)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--socket", default="/run/hackbank-audio/control.sock")
    parser.add_argument("--demo", action="store_true", help="Use in-memory development volumes")
    args = parser.parse_args()
    path = Path(args.socket)
    if path.exists():
        if not stat.S_ISSOCK(path.stat().st_mode):
            raise RuntimeError("Audio socket path is occupied by a regular file")
        path.unlink()
    with AudioServer(str(path), DemoAudio() if args.demo else PulseAudio()) as server:
        os.chmod(path, 0o660)
        server.serve_forever()


if __name__ == "__main__":
    main()
