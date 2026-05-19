from unittest import TestCase
from unittest.mock import patch, Mock
from plugins.sounds import sounds


class TestSounds(TestCase):
    def setUp(self):
        self.master_mock = Mock()
        self.sounds_instance = sounds("SID", self.master_mock)

    def test_hook_checkout_with_deposit(self):
        self.master_mock.receipt.receipt = [{"product": "deposit"}]
        with patch.object(self.sounds_instance.master, "send_message") as mock_send:
            self.sounds_instance.hook_checkout(None)
            mock_send.assert_any_call(False, "sound", "itsgone.wav")

    def test_help(self):
        self.assertEqual(self.sounds_instance.help(), {"sounds": "All sound commands"})

    def test_hook_checkout_without_deposit(self):
        self.master_mock.receipt.receipt = [{"product": "other"}]
        with patch.object(self.sounds_instance.master, "send_message") as mock_send:
            self.sounds_instance.hook_checkout(None)
            mock_send.assert_called_with(False, "sound", "katsjing.wav")

    def test_hook_balance_below_threshold(self):
        with patch.object(self.sounds_instance.master, "send_message") as mock_send:
            self.sounds_instance.hook_balance((None, None, -13.38, None))
            mock_send.assert_called_with(False, "sound", "sinterklaas.wav")

    def test_hook_balance_above_threshold(self):
        with patch.object(self.sounds_instance.master, "send_message") as mock_send:
            self.sounds_instance.hook_balance((None, None, -13.36, None))
            mock_send.assert_not_called()

    def test_showsounds(self):
        with patch.object(self.sounds_instance.master, "send_message") as mock_send:
            self.sounds_instance.showsounds()
            mock_send.assert_called()

    def test_input_valid_commands(self):
        commands = [
            "sounds",
            "ns",
            "vergaderen",
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

    def test_pre_input_non_abort(self):
        with patch.object(self.sounds_instance.master, "send_message") as mock_send:
            self.sounds_instance.pre_input("non_abort_command")
            mock_send.assert_called_with(False, "sound", "KDE_Beep_ClassicBeep.wav")

    def test_pre_input_abort_is_silent(self):
        with patch.object(self.sounds_instance.master, "send_message") as mock_send:
            self.sounds_instance.pre_input("abort")
            mock_send.assert_not_called()

    def test_hook_undo_is_noop(self):
        self.assertIsNone(self.sounds_instance.hook_undo((1, {}, [], "user")))

    def test_hook_wrong(self):
        with patch.object(self.sounds_instance.master, "send_message") as mock_send:
            self.sounds_instance.hook_wrong(None)
            mock_send.assert_called_with(False, "sound", "KDE_Beep_Beep.wav")

    def test_startup(self):
        assert self.sounds_instance.startup() is None
