from unittest import TestCase
from unittest.mock import patch, Mock
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from plugins.sounds import sounds
from pos_sound_settings import POSSoundSettings, DEFAULTS


class TestSounds(TestCase):
    def setUp(self):
        self.master_mock = Mock()
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.settings = POSSoundSettings(Path(directory.name) / "sounds.json")
        self.sounds_instance = sounds("SID", self.master_mock, self.settings)

    def test_hook_checkout_with_deposit(self):
        self.master_mock.receipt.receipt = [{"product": "deposit"}]
        with patch.object(self.sounds_instance.master, "send_message") as mock_send:
            self.sounds_instance.hook_checkout(None)
            mock_send.assert_any_call(False, "sound", "POS/deposit/itsgone.wav")

    def test_help(self):
        self.assertEqual(self.sounds_instance.help(), {"sounds": "All sound commands"})

    def test_hook_checkout_without_deposit(self):
        self.master_mock.receipt.receipt = [{"product": "other"}]
        with patch.object(self.sounds_instance.master, "send_message") as mock_send:
            self.sounds_instance.hook_checkout(None)
            mock_send.assert_called_with(False, "sound", "POS/sale/katsjing.wav")

    def test_hook_balance_below_threshold(self):
        with patch.object(self.sounds_instance.master, "send_message") as mock_send:
            self.sounds_instance.hook_balance((None, None, -13.38, None))
            mock_send.assert_called_with(
                False, "sound", "POS/insufficient_funds/sinterklaas.wav"
            )

    def test_hook_balance_above_threshold(self):
        with patch.object(self.sounds_instance.master, "send_message") as mock_send:
            self.sounds_instance.hook_balance((None, None, -13.36, None))
            mock_send.assert_not_called()

    def test_showsounds(self):
        with patch.object(self.sounds_instance.master, "send_message") as mock_send:
            self.sounds_instance.showsounds()
            mock_send.assert_called()
            menu = json.loads(mock_send.call_args_list[0].args[2])
            self.assertIn({"text": "yeet", "display": "Yeet"}, menu["custom"])

    def test_input_valid_commands(self):
        commands = [
            "sounds",
            "ns",
            "vergaderen",
            "vergaderenextreme",
            "vergaderen_extreme",
            "throw",
            "yeet",
            "killsounds",
            "groovesalad",
            "christmas",
            "blues",
            "louder",
            "quieter",
            "abort",
        ]
        for command in commands:
            with self.subTest(command=command):
                with patch.object(
                    self.sounds_instance.master, "send_message"
                ) as mock_send:
                    self.assertTrue(self.sounds_instance.input(command))
                    if command != "abort":
                        mock_send.assert_called()

    def test_input_noop_commands(self):
        for command in ("deuron", "deuroff", "kassaon", "kassaoff"):
            with self.subTest(command=command):
                self.assertIsNone(self.sounds_instance.input(command))

    def test_input_invalid_command(self):
        with patch.object(self.sounds_instance.master, "send_message") as mock_send:
            self.assertIsNone(self.sounds_instance.input("invalid_command"))
            mock_send.assert_not_called()

    def test_sound_commands_play_only_the_requested_sample(self):
        for command, sample in (
            ("ns", "soundboard/ns.wav"),
            ("vergaderen", "soundboard/vergaderen.mp3"),
            ("vergaderenextreme", "soundboard/vergaderen_extreme.wav"),
            ("vergaderen_extreme", "soundboard/vergaderen_extreme.wav"),
            ("throw", "soundboard/throw.wav"),
            ("yeet", "soundboard/yeet.wav"),
        ):
            with self.subTest(command=command):
                with patch.object(
                    self.sounds_instance.master, "send_message"
                ) as mock_send:
                    self.sounds_instance.pre_input(command)
                    self.assertTrue(self.sounds_instance.input(command))
                    mock_send.assert_called_once_with(False, "sound", sample)
                    mock_send.reset_mock()
                    self.sounds_instance.pre_input(" " + command + " ")
                    mock_send.assert_not_called()

    def test_pre_input_non_abort(self):
        with patch.object(self.sounds_instance.master, "send_message") as mock_send:
            self.sounds_instance.pre_input("non_abort_command")
            mock_send.assert_called_with(
                False, "sound", "POS/command/KDE_Beep_ClassicBeep.wav"
            )

    def test_pre_input_abort_and_sounds_navigation_are_silent(self):
        for command in ("abort", "sounds"):
            with self.subTest(command=command):
                with patch.object(
                    self.sounds_instance.master, "send_message"
                ) as mock_send:
                    self.sounds_instance.pre_input(command)
                    mock_send.assert_not_called()

    def test_hook_undo_is_noop(self):
        self.assertIsNone(self.sounds_instance.hook_undo((1, {}, [], "user")))

    def test_hook_wrong(self):
        with patch.object(self.sounds_instance.master, "send_message") as mock_send:
            self.sounds_instance.hook_wrong(None)
            mock_send.assert_called_with(False, "sound", "POS/error/KDE_Beep_Beep.wav")

    def test_startup(self):
        assert self.sounds_instance.startup() is None
        topic, encoded = self.master_mock.client.publish.call_args.args
        self.assertEqual(topic, "hack42bar/output/settings/sounds")
        self.assertEqual(
            {item["id"]: item["selected"] for item in json.loads(encoded)["features"]},
            DEFAULTS,
        )
        self.assertEqual(
            self.master_mock.client.publish.call_args.kwargs, {"qos": 1, "retain": True}
        )

    def test_setting_is_saved_before_preview_and_read_by_other_sessions(self):
        self.sounds_instance.configure(
            json.dumps(
                {"request": "choose-1", "feature": "deposit", "sound": "money.wav"}
            )
        )
        self.assertEqual(
            POSSoundSettings(self.settings.path).sample("deposit"),
            "POS/deposit/money.wav",
        )
        calls = self.master_mock.send_message.call_args_list
        reply = json.loads(calls[0].args[2])
        self.assertTrue(reply["ok"])
        self.assertEqual(reply["request"], "choose-1")
        self.assertEqual(calls[0].args[:2], (False, "sound_settings"))
        self.assertEqual(calls[1].args, (False, "sound", "POS/deposit/money.wav"))
        self.master_mock.callhook.assert_not_called()

    def test_all_feature_hooks_use_current_choices(self):
        for feature, sound in [
            ("command", "KDE_Beep_Beep.wav"),
            ("deposit", "money.wav"),
            ("sale", "cash_tycoon.wav"),
            ("insufficient_funds", "insufficient_funds.wav"),
        ]:
            self.settings.set(feature, sound)
        self.sounds_instance.pre_input("clubmate")
        self.master_mock.send_message.assert_called_with(
            False, "sound", "POS/command/KDE_Beep_Beep.wav"
        )
        self.master_mock.receipt.receipt = [{"product": "deposit"}]
        self.sounds_instance.hook_checkout(None)
        self.master_mock.send_message.assert_any_call(
            False, "sound", "POS/deposit/money.wav"
        )
        self.master_mock.send_message.assert_called_with(
            False, "sound", "POS/sale/cash_tycoon.wav"
        )
        self.sounds_instance.hook_balance(("Jos", 0, -20, 123))
        self.master_mock.send_message.assert_called_with(
            False, "sound", "POS/insufficient_funds/insufficient_funds.wav"
        )

    def test_invalid_setting_is_rejected_without_saving_or_previewing(self):
        for payload in [
            b"not-json",
            b"\xff",
            "[]",
            json.dumps(
                {"request": "bad-1", "feature": "sale", "sound": "../deposit/money.wav"}
            ),
            json.dumps({"request": "bad-2", "feature": [], "sound": "x.wav"}),
        ]:
            self.master_mock.reset_mock()
            self.sounds_instance.configure(payload)
            self.assertFalse(self.settings.path.exists())
            self.master_mock.send_message.assert_called_once()
            self.assertEqual(
                self.master_mock.send_message.call_args.args[:2],
                (False, "sound_settings"),
            )
            self.assertFalse(
                json.loads(self.master_mock.send_message.call_args.args[2])["ok"]
            )

    def test_preview_current_error_sound_without_saving(self):
        self.sounds_instance.configure('{"request":"preview-1","preview":"error"}')
        self.assertFalse(self.settings.path.exists())
        self.master_mock.send_message.assert_called_with(
            False, "sound", "POS/error/KDE_Beep_Beep.wav"
        )

    def test_read_and_reset_requests(self):
        self.sounds_instance.configure('{"request":"read-1"}')
        self.assertFalse(self.settings.path.exists())
        self.assertEqual(self.master_mock.send_message.call_count, 1)
        self.settings.set("sale", "cash_tycoon.wav")
        self.sounds_instance.configure('{"request":"reset-1","reset":"sale"}')
        self.master_mock.send_message.assert_called_with(
            False, "sound", "POS/sale/katsjing.wav"
        )
        self.sounds_instance.configure('{"request":"reset-2","reset":"all"}')
        self.master_mock.send_message.assert_called_with(
            False, "sound", "POS/command/KDE_Beep_ClassicBeep.wav"
        )
        self.assertEqual(
            {
                item["id"]: item["selected"]
                for item in self.settings.state()["features"]
            },
            DEFAULTS,
        )
