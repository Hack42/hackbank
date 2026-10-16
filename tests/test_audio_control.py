import http.client
import json
import socket
import subprocess
from tempfile import TemporaryDirectory
import threading
import unittest

from audio_control import AudioServer, DemoAudio, PulseAudio


class TestPulseAudio(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.sinks = [
            {"name": "hackbank_pos", "mute": False, "volume": {"left": {"value": 32768}, "right": {"value": 32768}}},
            {"name": "snapcast", "mute": True, "volume": {"left": {"value": 60293}, "right": {"value": 60293}}},
            {"name": "unrelated", "mute": False, "volume": {"left": {"value": 65536}}},
        ]

        def run(*args):
            self.calls.append(args)
            if args == ("-f", "json", "list", "sinks"):
                return json.dumps(self.sinks)
            sink = next(item for item in self.sinks if item["name"] == args[1])
            if args[0] == "set-sink-volume":
                level = round(int(args[2][:-1]) * 65536 / 100)
                sink["volume"] = {key: {"value": level} for key in sink["volume"]}
            elif args[0] == "set-sink-mute":
                sink["mute"] = args[2] == "1"
            return ""

        self.previews = []

        def play(sink):
            self.previews.append((sink, self.audio.read()))

        self.audio = PulseAudio(run=run, play=play)

    def test_reads_existing_outputs_and_external_changes(self):
        self.assertEqual(self.audio.read(), {"channels": {
            "pos": {"available": True, "volume": 50, "muted": False},
            "space": {"available": True, "volume": 92, "muted": True},
        }})
        self.sinks[0]["volume"] = {"left": {"value": 16384}}
        self.assertEqual(self.audio.read()["channels"]["pos"]["volume"], 25)

    def test_updates_only_requested_output_and_returns_confirmed_state(self):
        state = self.audio.set("space", 60)
        self.assertEqual(state["channels"]["space"], {"available": True, "volume": 60, "muted": False})
        self.assertEqual(state["channels"]["pos"]["volume"], 50)
        self.assertIn(("set-sink-volume", "snapcast", "60%"), self.calls)
        self.assertIn(("set-sink-mute", "snapcast", "0"), self.calls)
        self.assertFalse(any("unrelated" in call for call in self.calls))

    def test_zero_silences_output_and_missing_output_is_not_replaced(self):
        self.assertTrue(self.audio.set("pos", 0)["channels"]["pos"]["muted"])
        self.sinks = [item for item in self.sinks if item["name"] != "hackbank_pos"]
        self.assertEqual(self.audio.read()["channels"]["pos"], {"available": False, "volume": None, "muted": False})
        with self.assertRaises(RuntimeError):
            self.audio.set("pos", 40)

    def test_invalid_commands_cannot_reach_pactl(self):
        for channel, volume in [("default", 20), ("pos;echo bad", 30), ("pos", -1), ("space", 101), ("pos", True), ("pos", "50"), ("pos", 1.2)]:
            with self.subTest(channel=channel, volume=volume):
                with self.assertRaises(ValueError):
                    self.audio.set(channel, volume)
        self.assertEqual(self.calls, [])

    def test_preview_plays_only_on_requested_output_after_setting_its_volume(self):
        for channel, sink in [("pos", "hackbank_pos"), ("space", "snapcast")]:
            with self.subTest(channel=channel):
                state = self.audio.set(channel, 45, preview=True)
                played_sink, played_state = self.previews[-1]
                self.assertEqual(played_sink, sink)
                self.assertEqual(played_state["channels"][channel]["volume"], 45)
                self.assertFalse(played_state["channels"][channel]["muted"])
                self.assertTrue(state["preview_played"])

    def test_normal_updates_reads_and_zero_volume_do_not_play_a_preview(self):
        self.audio.read()
        self.audio.set("pos", 40)
        self.assertFalse(self.audio.set("pos", 0, preview=True)["preview_played"])
        self.assertEqual(self.previews, [])
        with self.assertRaises(ValueError):
            self.audio.set("pos", 50, preview="yes")

    def test_preview_failure_preserves_a_successful_volume_change(self):
        def fail(_sink):
            raise subprocess.CalledProcessError(1, "paplay")
        self.audio.play = fail
        state = self.audio.set("pos", 45, preview=True)
        self.assertEqual(state["channels"]["pos"]["volume"], 45)
        self.assertTrue(state["preview_error"])
        self.assertFalse(state["preview_played"])


class UnixConnection(http.client.HTTPConnection):
    def __init__(self, path):
        super().__init__("localhost", timeout=2)
        self.path = path

    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect(self.path)


class TestAudioAPI(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.path = self.temp.name + "/audio.sock"
        self.audio = DemoAudio()
        self.server = AudioServer(self.path, self.audio)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.temp.cleanup()

    def request(self, method, body=None, content_type="application/json", path="/volume"):
        connection = UnixConnection(self.path)
        connection.request(method, path, body=body, headers={"Content-Type": content_type})
        response = connection.getresponse()
        result = response.status, json.loads(response.read())
        connection.close()
        return result

    def test_socket_reads_and_changes_are_visible_to_another_client(self):
        self.assertEqual(self.request("GET")[1]["channels"]["pos"]["volume"], 35)
        status, state = self.request("POST", json.dumps({"channel": "pos", "volume": 68}))
        self.assertEqual(status, 200)
        self.assertEqual(state["channels"]["pos"]["volume"], 68)
        self.assertEqual(self.request("GET")[1]["channels"]["pos"]["volume"], 68)
        self.assertEqual(self.request("GET")[1]["channels"]["space"]["volume"], 70)

    def test_rejects_invalid_input_without_changing_state(self):
        initial = self.audio.read()
        for body in ['{"channel":"pos","volume":999}', '{"channel":"bad","volume":50}', '{"channel":"pos","volume":50,"preview":"yes"}', '{"channel":"pos","volume":50,"preview":true,"extra":1}', '[]', 'not-json', 'x' * 257]:
            self.assertEqual(self.request("POST", body)[0], 400)
        self.assertEqual(self.request("POST", "channel=pos&volume=20", "application/x-www-form-urlencoded")[0], 415)
        self.assertEqual(self.request("GET", path="/arbitrary-command")[0], 404)
        self.assertEqual(self.audio.read(), initial)

    def test_preview_requests_are_optional_and_channel_specific(self):
        status, state = self.request("POST", json.dumps({"channel": "space", "volume": 64, "preview": True}))
        self.assertEqual(status, 200)
        self.assertTrue(state["preview_played"])
        self.assertEqual(self.audio.previews, ["space"])
        self.request("GET")
        self.request("POST", json.dumps({"channel": "pos", "volume": 40, "preview": False}))
        self.request("POST", json.dumps({"channel": "space", "volume": 0, "preview": True}))
        self.assertEqual(self.audio.previews, ["space"])


if __name__ == "__main__":
    unittest.main()
